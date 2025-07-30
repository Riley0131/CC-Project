from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os, time, json, sys, tempfile
import tkinter as tk
from pathlib import Path

#set up chrome & Driver
chrome_opts = Options()
chrome_opts.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

#store profile data in a specific folder
profile_dir = tempfile.mkdtemp(prefix="selenium-")
chrome_opts.add_argument(f"--user-data-dir={profile_dir}")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_opts)

def canvasLogin():
    driver.get("https://canvas.uccs.edu/login")
    root = tk.Tk()
    root.title("Canvas Login")
    root.geometry("300x120")
    
    label = tk.Label(
        root,
        text="Once you have logged in press save password and press the button below",
        justify="center"
    )
    label.pack(pady=(15,5))
    
    btn = tk.Button(
        root,
        text="Continue",
        width=12,
        command=root.destroy
    )
    btn.pack(pady=(0,15))

    root.mainloop

#load canvas page
def auditCanvasPage(canvas_url):
    driver.get(canvas_url)
    time.sleep(5)  # wait for the page to load
    buttons = driver.find_elements(
        By.CSS_SELECTOR,
        "button.controls-button[aria-label='Disable Captions'],"
        "button.controls-button[aria-label='Enable Captions']"
    )

    return bool(buttons)
    

def getEmbeddedVideos(courseID):
    filePath = f"data/sortedModules/sorted_modules_{courseID}.json"
    videos = []
    if os.path.exists(filePath):
        with open(filePath, "r") as f:
            data = json.load(f)
        
        return data.get("canvas", [])
    else:
        print(f"Debug: No sorted modules found for course {courseID}")
        return []
    
def truncateCanvasUrl(links):
    return [link.replace("/api/v1", "") for link in links]

def main(courseID):
    # canvasLogin()
    embeddedVideos = getEmbeddedVideos(courseID)
    embeddedVideos = truncateCanvasUrl(embeddedVideos)
    results = []

    for video_url in embeddedVideos:
        has_captions = auditCanvasPage(video_url)
        results.append({
            "type": "canvas",
            "url": video_url,
            "has_captions": has_captions,
            "course_id": courseID
        })

    file_path = "data/audited_videos.json"

    # Load existing data or initialize an empty list
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.extend(results)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    #driver.quit()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python embeddedVideo.py <courseID>")
    else:
        main(sys.argv[1])

