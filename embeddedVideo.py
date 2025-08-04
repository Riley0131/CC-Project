from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os, time, json, sys, tempfile
import tkinter as tk
import chromeSetup

def make_driver(profile_dir: str):
    opts = Options()
    opts.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    # use your persistent profile
    opts.add_argument(f"--user-data-dir={profile_dir}")
    # stability flags
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)

def auditCanvasPage(driver, canvas_url: str) -> bool:
    driver.get(canvas_url)
    time.sleep(5)
    buttons = driver.find_elements(
        By.CSS_SELECTOR,
        "button.controls-button[aria-label='Disable Captions'],"
        "button.controls-button[aria-label='Enable Captions']"
    )
    return bool(buttons)

def getEmbeddedVideos(courseID: str):
    filePath = f"data/sortedModules/sorted_modules_{courseID}.json"
    if not os.path.exists(filePath):
        print(f"[!] No sorted modules for course {courseID}")
        return []
    with open(filePath) as f:
        return json.load(f).get("canvas", [])

def truncateCanvasUrl(links):
    return [link.replace("/api/v1", "") for link in links]

def main(courseID: str):
    # 1) Prepare profile folder
    profile_path = os.path.join(os.getcwd(), "selenium_profile")
    os.makedirs(profile_path, exist_ok=True)

    # 2) Launch browser once
    driver = make_driver(profile_path)

    # 3) Prompt user to log in (and save credentials)
    chromeSetup.canvasLogin(driver)

    # 4) Load your JSON-driven list of video URLs
    vids = truncateCanvasUrl(getEmbeddedVideos(courseID))

    # 5) Audit each one
    results = []
    for url in vids:
        results.append({
            "type": "canvas",
            "url": url,
            "has_captions": auditCanvasPage(driver, url),
            "course_id": courseID
        })

    # 6) Save or append to your output file
    out_path = "data/audited_videos.json"
    if os.path.exists(out_path):
        with open(out_path) as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    existing.extend(results)
    with open(out_path, "w") as f:
        json.dump(existing, f, indent=2)

    driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python embeddedVideo.py <courseID>")
        sys.exit(1)
    main(sys.argv[1])
