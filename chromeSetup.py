#!/usr/bin/env python3

import os
import tkinter as tk
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ─── Utilities ─────────────────────────────────────────────────────────────────

def clear_saved_passwords(profile_path):
    """
    Removes the Chrome 'Login Data' database where saved passwords live.
    """
    default_profile = os.path.join(profile_path, 'Default')
    login_db = os.path.join(default_profile, 'Login Data')
    if os.path.exists(login_db):
        os.remove(login_db)
        print(f"[+] Cleared saved passwords: removed {login_db}")
    else:
        print(f"[i] No existing Login Data found at {login_db}")

def canvasLogin(driver):
    """
    Opens the Canvas login page in the given WebDriver, then pops
    up a Tkinter window waiting for user confirmation.
    """
    driver.get("https://canvas.uccs.edu/login")
    root = tk.Tk()
    root.title("Canvas Login")
    root.geometry("320x130")
    root.resizable(False, False)

    label = tk.Label(
        root,
        text="Once you have logged in,\nclick 'Save' on the Chrome prompt,\nthen press Continue below.",
        justify="center",
        font=("Arial", 10)
    )
    label.pack(pady=(15, 5))

    btn = tk.Button(
        root,
        text="Continue",
        width=14,
        command=root.destroy
    )
    btn.pack(pady=(0, 15))

    root.mainloop()

# ─── Main Flow ────────────────────────────────────────────────────────────────

def main():
    # 1) Configure profile directory
    profile_path = os.path.join(os.getcwd(), 'selenium_profile')
    os.makedirs(profile_path, exist_ok=True)

    # 2) Clear any existing saved passwords
    clear_saved_passwords(profile_path)

    # 3) Start Chrome with that profile
    chrome_opts = Options()
    chrome_opts.add_argument(f"--user-data-dir={profile_path}")
    # chrome_opts.add_argument("--profile-directory=Default")  # usually implicit

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_opts)

    try:
        # 4) Navigate to Canvas and wait for user
        canvasLogin(driver)
        print("[✓] Detected user confirmation. Closing browser...")
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
