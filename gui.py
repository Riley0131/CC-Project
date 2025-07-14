from calendar import c
from ctypes.wintypes import SIZE
import tkinter as tk
from tkinter import W, Toplevel, messagebox, filedialog, Scrollbar, Text
import subprocess
import json
import os


def dataReset():
    subprocess.run(["python", "dataReset.py"])
    messagebox.showinfo("Reset", "Data has been reset successfully.")

def showAuditResults():
    messagebox.showinfo("Audit", "Running audit, this may take a while depending on the number of videos.")
    subprocess.run(["python", "runAudit.py"], capture_output=True, text=True)
    messagebox.showinfo("Audit Complete", "Audit completed successfully. Check the 'data' folder for results.")

def load_and_count_json():
    file_path = os.path.join("data", "audited_videos.json")
    if not file_path:
        return
    
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        has_captions_count = sum(1 for item in data if item.get("has_captions") is True)
        no_captions_count = sum(1 for item in data if item.get("has_captions") is False)

        messagebox.showinfo("Audit Summary", f"Videos with Captions: {has_captions_count}\nVideos without Captions: {no_captions_count}")
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process file: {e}")

def runIndividualAudit(ivCourseId):
    course = ivCourseId.get().strip()
    
    if not course:
        messagebox.showerror("Error", "Please enter a course ID.")
    else:
        subprocess.run(["python", "individualAudit.py", course])
        messagebox.showinfo("Audit Complete", f"Audit for course {course} completed successfully. Check the 'data' folder for results.")


def main():
    root = tk.Tk()

    # --- Modal Warning Window ---
    warningWindow = tk.Toplevel(root)
    warningWindow.title("In Development")
    warningWindow.geometry("350x200")
    warningWindow.transient(root)      # Tie it to the root window
    warningWindow.grab_set()           # Block interaction with root
    warningWindow.focus_force()        # Focus on warning window

    message = tk.Label(
        warningWindow,
        text="This tool is still under development. Please only use it as a tool to streamline the auditing process.\n\nCurrently there is a known issue where the program may present false negatives for some youtube videos.",
        wraplength=300,
        justify="center"
    )
    message.pack(pady=20)

    understandButton = tk.Button(
        warningWindow,
        text="I understand",
        command=warningWindow.destroy
    )
    understandButton.pack(pady=10)

    root.wait_window(warningWindow) 


    # GUI Setup
    
    root.title("UCCS Closed Captioning Audit")
    root.geometry("500x300")

    #title label
    title_label = tk.Label(root, text="UCCS Closed Captioning Audit", font=("Arial", 20))
    title_label.pack(pady=10)

    #run audit button
    runAuditButton = tk.Button(root, text="Run Complete Audit", command=showAuditResults)
    runAuditButton.pack(pady=10)

    courseEntry = tk.Label(root, text="Enter Course ID for Individual Audit:")
    courseEntry.pack(pady=5)
    #text entry for individual course audit
    ivCourseId = tk.Entry(root, width=30)
    ivCourseId.pack(pady=5)

    #run individual course audit button
    individualAuditButton = tk.Button(root, text="Run Individual Course Audit", command=lambda: runIndividualAudit(ivCourseId))
    individualAuditButton.pack(pady=10)

    #summarize json button
    jsonSummaryButton = tk.Button(root, text="Summarize results", command=load_and_count_json)
    jsonSummaryButton.pack(pady=10)

    #reset data button
    resetDataButton = tk.Button(root, text="Reset Data (WARNING: All existing data will be lost!)", command=dataReset, bg="red", fg="white")
    resetDataButton.pack(pady=10)



    root.mainloop()

if __name__ == "__main__":
    main()