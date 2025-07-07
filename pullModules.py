#Riley O'Shea
#University of Colorado Colorado Springs
#06/25/2025

#pulls user courses, seperates modules and urls by type.

import requests
from config.canvasAPI import CANVAS_API_TOKEN
import json

CANVAS_BASE_URL = "https://canvas.uccs.edu/api/v1"
HEADERS = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}



def get_courses():
    print("Debug: Fetching courses")
    courses = []
    url = f"{CANVAS_BASE_URL}/courses"

    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Error fetching courses: {response.status_code} - {response.text}")
            break

        batch = response.json()
        print(f"Debug: Fetched {len(batch)} courses")
        courses.extend(batch)

        # Parse pagination link
        links = response.headers.get("Link", "")
        next_url = None
        for link in links.split(","):
            if 'rel="next"' in link:
                next_url = link[link.find("<")+1:link.find(">")]
                break

        url = next_url

    return courses
    

def getCourseModules(course_id):
    #Fetches all modules for a specific course
    url = f"{CANVAS_BASE_URL}/courses/{course_id}/modules"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        response = response.json()
        items_urls = [module.get("items_url") for module in response]
        urls = [] #stores the urls of the items in the modules
        for items_url in items_urls:
            if items_url:
                items_response = requests.get(items_url, headers=HEADERS)
                if items_response.status_code == 200:
                    items = items_response.json()
                    for item in items:
                        if "url" in item:
                            urls.append(item["url"])
                        if "external_url" in item:
                            urls.append(item["external_url"])


        print(f"Debug: Found {len(urls)} URLs in course {course_id}")
        return urls
    
def sortUrls(urls):
    print("Debug: Sorting URLs")
    if not urls:
        print("Debug: No URLs to sort")
        return {"youtube": [], "canvas": [], "other": []}

    youtube = []
    canvas = []
    panopto = []
    other = []

    for u in urls:
        if not isinstance(u, str):
            print(f"Debug: Skipping non-string URL: {u}")
            continue
        if "youtu" in u:
            print(f"Debug: Found YouTube URL: {u}")
            youtube.append(u)
        elif "canvas" in u:
            print(f"Debug: Found Canvas URL: {u}")
            canvas.append(u)
        elif "panopto" in u:
            print(f"Debug: Found Pantopto URL: {u}")
            panopto.append(u)
        else:
            print(f"Debug: Found other URL: {u}")
            other.append(u)

    return {
        "youtube": youtube,
        "canvas": canvas,
        "panopto": panopto,
        "other": other
    }
            
    

def main():
    #get courses
    courses = get_courses()
    courses_ids = [course['id'] for course in courses]
    with open('data/courses.json', 'w') as f:
        json.dump(courses, f, indent=4)
   
    #save course ids
    with open('data/courses_ids.json', 'w') as f:
        json.dump(courses_ids, f, indent=4)

    
    #Pull modules for each course & sort
    for course in courses_ids:
        modules = getCourseModules(course)
        with open(f'data/courseModules/modules_{course}.json', 'w') as f:
            json.dump(modules, f, indent=4)


    for course in courses_ids:
        with open(f'data/courseModules/modules_{course}.json', 'r') as f:
            urls = json.load(f)
        sortedUrls = sortUrls(urls)
        with open(f'data/sortedModules/sorted_modules_{course}.json', 'w') as f:
            json.dump(sortedUrls, f, indent=4)


if __name__ == "__main__":
    main()