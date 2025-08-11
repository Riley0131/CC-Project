#Riley O'Shea
#University of Colorado Colorado Springs
#8/7/2025
## This is a test to try to further filter out non video embedded files using selenium

import json
import os
import sys
import tkinter as tk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def compileURLs(courses):
    """
    args:
        courses: list of course IDs to process
    returns:
        None
    Compiles a list of Canvas URLs to be audited for embedded videos.
    """
    for course in courses:
        path = f"data/sortedModules/sorted_modules_{course}.json"
        #ensure sorted modules file exists
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            #skip the course if the file doesn't exist
            print(f"  [!] JSON not found for course {course}, skipping.")
            continue
    
        #skip if no Canvas entries
        urls = data.get("canvas", [])
        if not urls:
            continue
        #filter videos


def jsonPrinter(hasCaptions, url):
    """
    args:
        hasCaptions: boolean indicating if captions are available
        url: the Canvas URL being audited
    returns:
        Prints results to audited_videos.json
    """
    #print results to audited_videos.json
    file_path = "data/audited_videos.json"
    j = {
        "type": "Canvas",
        "url": url,
        "has_captions": hasCaptions,
    }

    #load existing data or initialize an empty list
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Append new entry
    data.append(j)

    #write back to file
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def auditVideos(videos, timeout=2, headless=True):
    """
    args:
        videos: list of Canvas URLs to audit for embedded videos
        timeout: maximum wait time for elements to load (default 2 seconds)
        headless: whether to run Chrome in headless mode (default True)

    returns:
        isVideo: dictionary mapping URLs to whether they contain embedded videos
    This function uses Selenium to check each Canvas URL for embedded videos.
    """
    #configure chrome
    chrome_opts = Options()
    # if headless:
    #     chrome_opts.add_argument("--headless=new")

    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--no-sandbox")

    #start driver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_opts
    )

    #allow user to log in
    driver.get("https://canvas.uccs.edu/login")
    #input("Please log in to Canvas and then press Enter to continue...")
    root = tk.Tk()
    root.title("Please Log Into Canvas")
    root.geometry("300x100")
    Label = tk.Label(root, text="Please log into Canvas then press Continue.")
    Label.pack(pady=20)
    button = tk.Button(root, text="Continue", command=root.destroy)
    button.pack(pady=10)
    root.mainloop()

    isVideo = {}

    try:
        for url in videos:
            driver.get(url)
            try:
                #check for video element
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.ID, "media_preview"))
                )

                #check for captions button
                try:
                    WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((
                            By.CSS_SELECTOR,
                            "button.controls-button[aria-label='Enable Captions']"
                        ))
                    )
                    captions_enabled = True
                    jsonPrinter(captions_enabled, url)  # save result to JSON

                except TimeoutException:
                    captions_enabled = False
                    jsonPrinter(captions_enabled, url)  # save result to JSON

                

                isVideo[url] = True
            except TimeoutException:
                isVideo[url] = False

    finally:
        driver.quit()

    return isVideo


def truncateCanvasUrl(links):
    return [link.replace("/api/v1", "") for link in links]


def main(courses):
    """
    For each course ID in `courses`, read its sorted_modules JSON,
    extract the Canvas URLs, filter to only those with embedded video,
    and then collect all those “true” URLs into one list.
    """

    all_canvas_with_video = []

    # iterate over each course
    for course in courses:
        path = f"data/sortedModules/sorted_modules_{course}.json"
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"  [!] JSON not found for course {course}, skipping.")
            continue

        # get canvas URLs for this course
        urls = data.get("canvas", [])
        urls = truncateCanvasUrl(urls)  # truncate per course

        if not urls:
            continue

        # add to the master list
        all_canvas_with_video.extend(urls)

    auditVideos(all_canvas_with_video)  # audit all collected Canvas URLs



    


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sortEmbeddedVideos.py <courseID1> <courseID2> ...")
    else:
        courses = sys.argv[1:]
        main(courses)