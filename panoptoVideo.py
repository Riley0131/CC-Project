"""Panopto caption auditor.

This module queries the Canvas API for external Panopto player links
(``Embed.aspx``/``Viewer.aspx``) and records whether captions are available. It
drives Selenium to open each discovered URL and scan the player UI for caption
controls before falling back to the Panopto REST API when Selenium cannot
determine an answer.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import parse_qs, urlparse, urlunparse

try:  # GUI prompt for manual authentication if Selenium needs it
    import tkinter as tk
except Exception:  # pragma: no cover - headless environments may not provide Tk
    tk = None  # type: ignore

import requests
import pullModules
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
    fragment = (parsed.fragment or "").lower()
    lower_path = path.lower()

    if "embed.aspx" in lower_path and "access_token" not in fragment:
        updated_path = re.sub(r"embed\.aspx", "Viewer.aspx", path, flags=re.IGNORECASE)
        parsed = parsed._replace(path=updated_path)
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


def _is_panopto_player_url(url: str) -> bool:
    if not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    netloc = (parsed.netloc or "").lower()
    path = (parsed.path or "").lower()

    if "panopto" not in netloc:
        return False

    if "/panopto/pages/" not in path:
        return False

    return any(keyword in path for keyword in ("embed.aspx", "viewer.aspx", "auth/viewer.aspx"))


def _fetch_panopto_links_from_canvas(course_id: str) -> List[str]:
    try:
        module_urls = pullModules.getCourseModules(course_id)
    except Exception as exc:
        print(f"Error retrieving module URLs from Canvas for course {course_id}: {exc}")
        return []

    if not module_urls:
        return []

    sorted_urls = pullModules.sortUrls(module_urls)
    candidates = []

    if isinstance(sorted_urls, dict):
        raw_candidates = sorted_urls.get("panopto") or []
        if isinstance(raw_candidates, list):
            candidates = [u for u in raw_candidates if _is_panopto_player_url(u)]

    return candidates


def _fetch_panopto_links_from_cache(course_id: str) -> List[str]:
    path = f"data/sortedModules/sorted_modules_{course_id}.json"
    payload = _load_json_file(path)
    if not isinstance(payload, dict):
        return []

    urls = payload.get("panopto")
    if not isinstance(urls, list):
        return []

    return [url for url in urls if _is_panopto_player_url(url)]


def _iter_panopto_links(courses: Iterable[str]) -> List[Tuple[str, str]]:
    """Return a ``[(course_id, url), …]`` list for Panopto links."""

    results: List[Tuple[str, str]] = []

    for course in courses:
        course_id = str(course)
        seen: Set[str] = set()

        urls = _fetch_panopto_links_from_canvas(course_id)
        if not urls:
            urls = _fetch_panopto_links_from_cache(course_id)

        if not urls:
            continue

        for url in urls:
            if not isinstance(url, str):
                continue

            normalized = _normalize_panopto_url(url)
            session_id = _extract_session_id(url) or _extract_session_id(normalized)
            canonical = session_id or normalized

            if canonical in seen:
                continue

            seen.add(canonical)
            results.append((course_id, url))

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
        visit_url = _normalize_panopto_url(url)
        base_url = self._base_url(visit_url)
        session_id = _extract_session_id(url) or _extract_session_id(visit_url)

        selenium_result = self._check_via_selenium(base_url, visit_url)
        if selenium_result is True:
            return True

        api_result: Optional[bool] = None
        if base_url and session_id:
            api_result = self._check_via_api(base_url, session_id)

        if selenium_result is False:
            return True if api_result is True else False

        if selenium_result is None:
            if api_result is not None:
                return api_result
            return False

        return api_result if api_result is not None else False

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

    def _check_via_selenium(self, base_url: Optional[str], url: str) -> Optional[bool]:
        driver = self._ensure_driver(base_url)
        if not driver:
            print("Selenium driver could not be started; falling back to API if available.")
            return None

        try:
            driver.get(url)
        except WebDriverException as exc:
            print(f"Error loading Panopto URL {url}: {exc}")
            return None

        try:
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            print(f"Timed out waiting for Panopto player to load for {url}")
            return None

        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        found = self._scan_for_captions(driver)

        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        return True if found else False

    def _scan_for_captions(self, driver: webdriver.Chrome, depth: int = 0) -> bool:
        if depth > 5:
            return False

        if self._captions_present(driver):
            return True

        try:
            frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
        except Exception:
            frames = []

        for frame in frames:
            found = False
            try:
                WebDriverWait(driver, self.timeout).until(
                    EC.frame_to_be_available_and_switch_to_it(frame)
                )
                found = self._scan_for_captions(driver, depth + 1)
            except TimeoutException:
                continue
            finally:
                try:
                    driver.switch_to.parent_frame()
                except Exception:
                    driver.switch_to.default_content()

            if found:
                return True

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
        keywords = ("caption", "captions", "subtitle", "subtitles")

        def _contains_keyword(value: Optional[str]) -> bool:
            if not value:
                return False

            value_lower = value.lower()
            if any(keyword in value_lower for keyword in keywords):
                return True

            return bool(re.search(r"\bcc\b", value_lower))

        try:
            interactive_elements = driver.find_elements(
                By.XPATH,
                "//button | //a | //div | //span | //*[@aria-label or @title or @data-tooltip or @data-original-title or @class or @id]",
            )
        except Exception:
            interactive_elements = []

        for element in interactive_elements:
            attributes = [
                element.get_attribute("aria-label"),
                element.get_attribute("title"),
                element.get_attribute("data-tooltip"),
                element.get_attribute("data-original-title"),
                element.get_attribute("data-testid"),
                element.get_attribute("data-qa"),
                element.get_attribute("class"),
                element.get_attribute("id"),
                element.text,
            ]

            if any(_contains_keyword(value) for value in attributes):
                return True

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
