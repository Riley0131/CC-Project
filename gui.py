#Riley O'Shea
#University of Colorado Colorado Springs
#7/29/25
#Graphical User Interface, this is the head of the program that allows the user to run audits, delete and manage data, or make changes to the api key from a GUI


import tkinter as tk
from tkinter import messagebox
import subprocess
import json
import os
import re

def dataReset():
    subprocess.run(["python", "dataReset.py"])
    messagebox.showinfo("Reset", "Data has been reset successfully.")


def showAuditResults():
    messagebox.showinfo("Audit", "Running audit, this may take a while depending on the number of videos.")
    subprocess.run(["python", "runAudit.py"], capture_output=True, text=True)
    messagebox.showinfo("Audit Complete", "Audit completed successfully. Check the 'data' folder for results.")


def load_and_count_json():
    file_path = os.path.join("data", "audited_videos.json")
    if not os.path.exists(file_path):
        messagebox.showerror("Error", "No audit data found.")
        return
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        has_captions_count = sum(1 for item in data if item.get("has_captions") is True)
        no_captions_count = sum(1 for item in data if item.get("has_captions") is False)

        messagebox.showinfo(
            "Audit Summary",
            f"Videos with Captions: {has_captions_count}\nVideos without Captions: {no_captions_count}"
        )
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process file: {e}")


def runIndividualAudit(course_id):
    subprocess.run(["python", "individualAudit.py", course_id])
    messagebox.showinfo(
        "Audit Complete",
        f"Audit for course {course_id} completed successfully. Check the 'data' folder for results."
    )


def loadCanvasAPIToken():
    config_path = os.path.join(os.path.dirname(__file__), "config", "canvasAPI.py")
    try:
        with open(config_path, "r") as f:
            for line in f:
                match = re.match(r"^CANVAS_API_TOKEN\s*=\s*['\"](.*)['\"]", line)
                if match:
                    return match.group(1)
    except Exception:
        pass
    return ""


def saveCanvasAPIToken(token):
    config_path = os.path.join(os.path.dirname(__file__), "config", "canvasAPI.py")
    try:
        with open(config_path, "r") as f:
            lines = f.readlines()
        with open(config_path, "w") as f:
            for line in lines:
                if line.startswith("CANVAS_API_TOKEN"):
                    f.write(f'CANVAS_API_TOKEN = "{token}"\n')
                else:
                    f.write(line)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save token: {e}")
        return False


def main():
    root = tk.Tk()

    # --- Modal Warning Window ---
    warningWindow = tk.Toplevel(root)
    warningWindow.title("In Development")
    warningWindow.geometry("350x200")
    warningWindow.transient(root)
    warningWindow.grab_set()
    warningWindow.focus_force()

    msg = (
        "This tool is still under development. Please only use it as a tool to streamline the auditing process."
        "\n\nCurrently there is a known issue where the program may present false negatives for some youtube videos."
    )
    tk.Label(warningWindow, text=msg, wraplength=300, justify="center").pack(pady=20)
    tk.Button(warningWindow, text="I understand", command=warningWindow.destroy).pack(pady=10)
    root.wait_window(warningWindow)

    # GUI Setup
    root.title("UCCS Closed Captioning Audit")
    root.geometry("500x350")

    tk.Label(root, text="UCCS Closed Captioning Audit", font=("Arial", 20)).pack(pady=10)
    tk.Button(root, text="Run Complete Audit", command=showAuditResults).pack(pady=10)

    def promptIndividualAudit():
        popup = tk.Toplevel(root)
        popup.title("Individual Course Audit")
        popup.geometry("350x150")
        popup.transient(root)
        popup.grab_set()

        tk.Label(popup, text="Enter Course ID:").pack(pady=5)
        entry = tk.Entry(popup, width=30)
        entry.pack(pady=5)

        def confirm():
            course = entry.get().strip()
            if not course:
                messagebox.showerror("Error", "Please enter a course ID.")
                return
            popup.destroy()
            runIndividualAudit(course)

        tk.Button(popup, text="Confirm", command=confirm).pack(pady=5)
        tk.Button(popup, text="Cancel", command=popup.destroy).pack()
        popup.wait_window()

    def promptSettings():
        popup = tk.Toplevel(root)
        popup.title("Settings")
        popup.geometry("400x200")
        popup.transient(root)
        popup.grab_set()

        tk.Label(popup, text="Canvas API Token:").pack(pady=5)
        token_entry = tk.Entry(popup, width=50)
        token_entry.insert(0, loadCanvasAPIToken())
        token_entry.pack(pady=5)

        def save_and_close():
            new_token = token_entry.get().strip()
            if saveCanvasAPIToken(new_token):
                messagebox.showinfo("Settings", "Token saved successfully.")
                popup.destroy()

        tk.Button(popup, text="Save", command=save_and_close).pack(pady=5)
        tk.Button(popup, text="Cancel", command=popup.destroy).pack()
        popup.wait_window()

    # Main buttons
    tk.Button(root, text="Run Individual Course Audit", command=promptIndividualAudit).pack(pady=10)
    tk.Button(root, text="Summarize results", command=load_and_count_json).pack(pady=10)
    tk.Button(root, text="Settings", command=promptSettings).pack(pady=10)
    tk.Button(root,
              text="Reset Data (WARNING: All existing data will be lost!)",
              command=dataReset,
              bg="red", fg="white").pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
