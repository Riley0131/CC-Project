"""Panopto caption auditor.

This module inspects Panopto links discovered during the Canvas course scan and
records whether captions are available. It first attempts to query the Panopto
REST API using the OAuth client configured in ``config/panoptoKey.py``. If the
API request fails (for example, because credentials are missing or insufficient
permissions), it falls back to Selenium automation to look for caption controls
in the embedded player UI.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse, urlunparse

try:  # GUI prompt for manual authentication if Selenium needs it
    import tkinter as tk
except Exception:  # pragma: no cover - headless environments may not provide Tk
    tk = None  # type: ignore

import requests
from requests.auth import HTTPBasicAuth
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

try:
    from config import panoptoKey as panopto_config
except Exception:  # pragma: no cover - configuration file may be missing in tests
    panopto_config = None


CLIENT_ID: str = getattr(panopto_config, "Client_ID", "") if panopto_config else ""
CLIENT_SECRET: str = getattr(panopto_config, "Client_Secret", "") if panopto_config else ""


def _load_json_file(path: str) -> Optional[dict]:
    try:
        with open(path, "r") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def _append_result(entry: dict, file_path: str = "data/audited_videos.json") -> None:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, FileNotFoundError):
            data = []
    else:
        data = []

    data.append(entry)

    with open(file_path, "w") as handle:
        json.dump(data, handle, indent=4)


def _normalize_panopto_url(url: str) -> str:
    """Convert embed links to the viewer format to simplify Selenium automation."""

    try:
        parsed = urlparse(url)
    except Exception:
        return url

    path = parsed.path or ""
    if "Embed.aspx" in path:
        path = path.replace("Embed.aspx", "Viewer.aspx")
        parsed = parsed._replace(path=path)
        return urlunparse(parsed)

    return url


def _extract_session_id(url: str) -> Optional[str]:
    try:
        parsed = urlparse(url)
    except Exception:
        return None

    query = parse_qs(parsed.query)
    if "id" in query and query["id"]:
        return query["id"][0]

    # Some Panopto links expose the session id as the final path segment
    segments = [segment for segment in parsed.path.split("/") if segment]
    for segment in reversed(segments):
        if len(segment) >= 32 and segment.count("-") >= 4:
            return segment

    return None


def _iter_panopto_links(courses: Iterable[str]) -> List[Tuple[str, str]]:
    """Return a ``[(course_id, url), …]`` list for Panopto links."""

    results: List[Tuple[str, str]] = []

    for course in courses:
        path = f"data/sortedModules/sorted_modules_{course}.json"
        payload = _load_json_file(path)
        if not payload:
            continue

        urls = payload.get("panopto") if isinstance(payload, dict) else None
        if not urls:
            continue

        seen: set[str] = set()
        for url in urls:
            if not isinstance(url, str):
                continue
            normalized = _normalize_panopto_url(url)
            if normalized in seen:
                continue
            seen.add(normalized)
            results.append((str(course), normalized))

    return results


def _has_caption_text(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_has_caption_text(item) for item in value)
    if isinstance(value, dict):
        return any(_has_caption_text(v) for v in value.values())
    return False


@dataclass
class _ApiToken:
    token: str
    expires_at: float


class PanoptoAuditor:
    """Audit helper that caches API tokens and the Selenium driver."""

    def __init__(self, client_id: str, client_secret: str, timeout: int = 15) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._tokens: Dict[str, _ApiToken] = {}
        self._session = requests.Session()
        self._driver: Optional[webdriver.Chrome] = None
        self._driver_base: Optional[str] = None

    # ------------------------------------------------------------------
    # public helpers
    def audit(self, url: str) -> bool:
        base_url = self._base_url(url)
        session_id = _extract_session_id(url)

        if base_url and session_id:
            api_result = self._check_via_api(base_url, session_id)
            if api_result is not None:
                return api_result

        return self._check_via_selenium(base_url, url)

    def close(self) -> None:
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
        self._driver = None
        self._driver_base = None
        try:
            self._session.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # context manager support
    def __enter__(self) -> "PanoptoAuditor":
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    @staticmethod
    def _base_url(url: str) -> Optional[str]:
        try:
            parsed = urlparse(url)
        except Exception:
            return None

        if not parsed.scheme or not parsed.netloc:
            return None

        return f"{parsed.scheme}://{parsed.netloc}"

    def _check_via_api(self, base_url: str, session_id: str) -> Optional[bool]:
        if not self.client_id or not self.client_secret:
            return None

        token = self._get_token(base_url)
        if not token:
            return None

        url = f"{base_url}/Panopto/api/v1/sessions/{session_id}/captions"
        try:
            response = self._session.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            print(f"Error contacting Panopto API for {session_id}: {exc}")
            return None

        if response.status_code == 200:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text

            return _has_caption_text(payload)

        if response.status_code in {204, 404}:
            return False

        print(
            f"Panopto API call for session {session_id} returned {response.status_code}: {response.text[:120]}"
        )
        return None

    def _get_token(self, base_url: str) -> Optional[str]:
        token = self._tokens.get(base_url)
        if token and time.time() < token.expires_at:
            return token.token

        data = {"grant_type": "client_credentials", "scope": "api"}
        token_url = f"{base_url}/Panopto/oauth2/connect/token"

        try:
            response = self._session.post(
                token_url,
                data=data,
                auth=HTTPBasicAuth(self.client_id, self.client_secret),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            print(f"Error requesting Panopto token: {exc}")
            return None

        if response.status_code != 200:
            print(
                f"Panopto token request failed ({response.status_code}): {response.text[:120]}"
            )
            return None

        try:
            payload = response.json()
        except ValueError:
            print("Panopto token response was not valid JSON.")
            return None

        token_value = payload.get("access_token")
        expires_in = payload.get("expires_in", 0)

        if not token_value:
            return None

        expiry = time.time() + max(int(expires_in) - 30, 0)
        self._tokens[base_url] = _ApiToken(token_value, expiry)
        return token_value

    def _check_via_selenium(self, base_url: Optional[str], url: str) -> bool:
        driver = self._ensure_driver(base_url)
        if not driver:
            print("Selenium driver could not be started; assuming captions unavailable.")
            return False

        try:
            driver.get(url)
        except WebDriverException as exc:
            print(f"Error loading Panopto URL {url}: {exc}")
            return False

        try:
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            return False

        if self._captions_present(driver):
            return True

        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for frame in frames:
            try:
                WebDriverWait(driver, self.timeout).until(
                    EC.frame_to_be_available_and_switch_to_it(frame)
                )
            except TimeoutException:
                continue

            try:
                if self._captions_present(driver):
                    driver.switch_to.default_content()
                    return True
            finally:
                driver.switch_to.default_content()

        return False

    def _ensure_driver(self, base_url: Optional[str]) -> Optional[webdriver.Chrome]:
        if self._driver and base_url and base_url != self._driver_base:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None
            self._driver_base = None

        if self._driver:
            return self._driver

        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        try:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options,
            )
        except WebDriverException as exc:
            print(f"Unable to start ChromeDriver: {exc}")
            return None

        self._driver = driver
        self._driver_base = base_url

        if base_url:
            try:
                driver.get(base_url)
            except WebDriverException:
                pass

        self._prompt_for_login()
        return driver

    def _prompt_for_login(self) -> None:
        message = (
            "Please log into Panopto in the opened browser window, then click Continue."
        )

        if tk is None:
            try:
                input(message + "\nPress Enter here once the login is complete...")
            except EOFError:
                pass
            return

        root = tk.Tk()
        root.title("Panopto Login Required")
        root.geometry("360x140")
        label = tk.Label(root, text=message, wraplength=320, justify="center")
        label.pack(pady=20)
        tk.Button(root, text="Continue", command=root.destroy).pack(pady=5)
        root.mainloop()

    @staticmethod
    def _captions_present(driver: webdriver.Chrome) -> bool:
        # Look for <track> elements that expose captions/subtitles
        try:
            tracks = driver.find_elements(By.TAG_NAME, "track")
        except Exception:
            tracks = []

        for track in tracks:
            kind = (track.get_attribute("kind") or "").lower()
            src = track.get_attribute("src")
            if kind in {"captions", "subtitles"} and src:
                return True

        try:
            elements = driver.find_elements(By.XPATH, "//*[@aria-label or @class or normalize-space(text())]")
        except Exception:
            elements = []

        for element in elements:
            label = (element.get_attribute("aria-label") or "").lower()
            classes = (element.get_attribute("class") or "").lower()
            text = (element.text or "").lower()
            combined = " ".join(part for part in [label, classes, text] if part)
            if any(keyword in combined for keyword in ("captions", "subtitle", "subtitles", "cc")):
                return True

        return False


def _load_course_ids() -> List[str]:
    payload = _load_json_file("data/courses_ids.json")
    if isinstance(payload, list):
        return [str(item) for item in payload]
    return []


def main(courses: Optional[Sequence[str]] = None, include_course_ids: bool = False) -> None:
    """Audit Panopto videos for the provided course ids."""

    if courses is None:
        courses = _load_course_ids()

    if not courses:
        print("Debug: No courses supplied for Panopto audit.")
        return

    videos = _iter_panopto_links(courses)
    if not videos:
        print("Debug: No Panopto videos found to audit.")
        return

    with PanoptoAuditor(CLIENT_ID, CLIENT_SECRET) as auditor:
        for course_id, url in videos:
            has_captions = auditor.audit(url)
            entry = {
                "type": "panopto",
                "url": url,
                "has_captions": has_captions,
            }
            if include_course_ids:
                entry["course_id"] = course_id

            _append_result(entry)


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    main()
