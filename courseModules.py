import requests
from config.canvasAPI import CANVAS_API_TOKEN
from youtube_transcript_api import YouTubeTranscriptApi 
from colorama import Fore, Back, Style
import tkinter as tk
import time
from tkinter import messagebox

CANVAS_BASE_URL = "https://canvas.uccs.edu/api/v1"
HEADERS = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
course_id = 165356

def get_all_courses():
    """Retrieve all courses the student is enrolled in, handling pagination."""
    url = f"{CANVAS_BASE_URL}/courses"
    course_list = []

    while url:
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            courses = response.json()
            for course in courses:
                course_id = course['id']
                course_name = course.get('name', f"Course {course_id}")
                course_list.append((course_id, course_name))

            # Handle pagination
            url = None  # Reset URL unless we find a next page
            if 'next' in response.links:
                url = response.links['next']['url']
        else:
            print(f"Error fetching courses: {response.status_code} - {response.text}")
            break

    return course_list

def get_course_files(course_id):
    """Retrieve all files and external links from a Canvas course."""
    url = f"{CANVAS_BASE_URL}/courses/{course_id}/modules"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        modules = response.json()
        external_links = []
        for module in modules:
            module_id = module['id']
            items_url = f"{CANVAS_BASE_URL}/courses/{course_id}/modules/{module_id}/items"
            time.sleep(0.5)  # Prevent rate limiting
            items_response = requests.get(items_url, headers=HEADERS)

            if items_response.status_code == 200:
                items = items_response.json()
                for item in items:
                    if item['type'] == 'ExternalUrl':
                        external_links.append(item['external_url'])
            else:
                print(f"Error {items_response.status_code}: {items_response.text}")

        return modules, external_links
    else:
        print(f"Error {response.status_code}: {response.text}")
        return [], []

def get_course_modules(course_id):
    """Retrieve all modules and their files for a course."""
    url = f"{CANVAS_BASE_URL}/courses/{course_id}/modules"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return []

    modules = response.json()
    for module in modules:
        module_id = module["id"]
        module["items"] = get_module_items(course_id, module_id)

    return modules

def get_module_items(course_id, module_id):
    """Retrieve all items in a module, including files and links."""
    url = f"{CANVAS_BASE_URL}/courses/{course_id}/modules/{module_id}/items"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return []

    return response.json()  # This includes all items (files, links, assignments, etc.)

def check_youtube_captions(video_url):
    """Check if a YouTube video has closed captions."""
    video_id = video_url.replace('https://www.youtube.com/watch?v=', '').replace('https://youtu.be/', '')  
    try:
        srt = YouTubeTranscriptApi.get_transcript(video_url)
        return bool(srt)
    except Exception:  # Catches TranscriptsDisabled and any other errors
        return False

def check_courses(courses):
    with open("CC Audit Report.txt", "w", encoding="utf-8") as report_file:
        for course in courses:
            course_id = course[0]  # Get course ID
            report_file.write(f"{course[1]}\n")  # Write course name to file

            # Fetch all files for this course
            files = get_course_files(course_id)
            report_file.write(f"  Found {len(files)} files in course\n")

            # Fetch all modules
            modules = get_course_modules(course_id)
            for module in modules:
                report_file.write(f"  Module: {module['name']}\n")

                # Fetch module items (files, links, etc.)
                module_items = get_module_items(course_id, module["id"])
                for item in module_items:
                    report_file.write(f"    - {item['title']} ({item['type']})\n")

                time.sleep(0.5)  # Prevent hitting API rate limits


def audit_all_courses():
    courses = get_all_courses()
    check_courses(courses)

def audit_individual_course(course_id_entry):
    course_id = course_id_entry.get().strip()
    
    if not course_id or course_id == "Enter course ID" or not course_id.isdigit():
        messagebox.showerror("Error", "Please enter a valid numeric course ID")
        return

    check_courses([(course_id, f"Course {course_id}")])
    


def gui():
    root = tk.Tk()
    root.title("UCCS Closed Captioning Audit")
    root.geometry("800x600")

    # Label
    title_label = tk.Label(root, text="UCCS Closed Captioning Audit", font=("Arial", 24, "bold"))
    title_label.pack(pady=10)

    # Button to audit all courses
    label = tk.Label(root, text="Click the button below to audit all courses for closed captions.", font=("Arial", 16))
    label.pack(pady=5)
    audit_all_button = tk.Button(root, text="Audit All User Courses", command=audit_all_courses)
    audit_all_button.pack(pady=5)

    # Button to audit a specific course
    label = tk.Label(root, text="Click the button below to audit a specific course:", font=("Arial", 16))
    label.pack(pady=5)
    audit_specific = tk.Button(root, text="Audit a Specific Course", command=lambda: audit_individual_course(course_id_entry))
    audit_specific.pack(pady=5)

    # Entry for course ID
    course_id_entry = tk.Entry(root, width=30)
    course_id_entry.insert(0, "Enter course ID")
    course_id_entry.pack(pady=5)

    root.mainloop()

def main():
    gui()
    

if __name__ == "__main__":
    main()
    