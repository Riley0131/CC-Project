#Riley O'Shea
#University of Colorado Colorado Springs
#06/25/2025

#pulls user courses, seperates modules and urls by type.

import requests
from config.canvasAPI import CANVAS_API_TOKEN
import json

CANVAS_BASE_URL = "https://canvas.uccs.edu/api/v1"
HEADERS = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}


def _get_next_link(link_header):
    """Return the ``rel=next`` URL from a Canvas pagination header."""

    if not link_header:
        return None

    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue

        start = section.find("<")
        end = section.find(">", start + 1)
        if start != -1 and end != -1:
            return section[start + 1 : end]

    return None


#retrieves all courses that the user is enrolled in
def get_courses():
    '''Fetches all courses the user is enrolled in from Canvas API.'''
    print("Debug: Fetching courses")
    courses = []
    url = f"{CANVAS_BASE_URL}/courses"
    params = {"per_page": 100}

    while url:
        request_kwargs = {"headers": HEADERS}
        if params is not None and "?" not in url:
            request_kwargs["params"] = params

        response = requests.get(url, **request_kwargs)
        if response.status_code != 200:
            print(f"Error fetching courses: {response.status_code} - {response.text}")
            break

        batch = response.json()
        print(f"Debug: Fetched {len(batch)} courses")
        courses.extend(batch)

        url = _get_next_link(response.headers.get("Link", ""))
        params = None

    return courses

#Fetches all modules for a specific course
def getCourseModules(course_id):
    """Fetches all modules for a specific course from Canvas API.
    Args:
        course_id (int): The ID of the course to fetch modules for.
    Returns:
        list: A list of URLs for items in the course modules.
    """
    urls = []  # stores the urls of the items in the modules
    url = f"{CANVAS_BASE_URL}/courses/{course_id}/modules"
    params = {"per_page": 100}

    while url:
        request_kwargs = {"headers": HEADERS}
        if params is not None:
            request_kwargs["params"] = params

        response = requests.get(url, **request_kwargs)
        if response.status_code != 200:
            print(
                f"Error fetching modules for course {course_id}: {response.status_code} - {response.text}"
            )
            break

        payload = response.json()
        items_urls = [module.get("items_url") for module in payload]

        for items_url in items_urls:
            if not items_url:
                continue

            item_url = items_url
            item_params = {"per_page": 100}

            while item_url:
                item_kwargs = {"headers": HEADERS}
                if item_params is not None and "?" not in item_url:
                    item_kwargs["params"] = item_params

                items_response = requests.get(item_url, **item_kwargs)
                if items_response.status_code != 200:
                    print(
                        f"Error fetching module items for course {course_id}: {items_response.status_code} - {items_response.text}"
                    )
                    break

                items = items_response.json()
                for item in items:
                    link = item.get("url")
                    external = item.get("external_url")

                    # For Panopto videos, follow the Canvas API url field to get the direct link
                    if link and "panopto" in link.lower():
                        try:
                            # Make an additional API call to the Canvas module item URL
                            link_response = requests.get(link, headers=HEADERS)
                            if link_response.status_code == 200:
                                link_data = link_response.json()
                                # Extract the url field from the response
                                direct_url = link_data.get("url")
                                if direct_url:
                                    urls.append(direct_url)
                                    print(f"Debug: Followed Canvas API for Panopto link: {direct_url}")
                                else:
                                    # Fallback to original link if no url field found
                                    urls.append(link)
                            else:
                                # Fallback to original link if API call fails
                                urls.append(link)
                        except Exception as e:
                            print(f"Error following Canvas API for link {link}: {e}")
                            # Fallback to original link
                            urls.append(link)
                    elif link:
                        urls.append(link)

                    if external:
                        urls.append(external)

                item_url = _get_next_link(items_response.headers.get("Link", ""))
                item_params = None

        url = _get_next_link(response.headers.get("Link", ""))
        params = None

    print(f"Debug: Found {len(urls)} URLs in course {course_id}")
    return urls
    
def sortUrls(urls):
    """
    Sorts the different url's based on type
    args:
        urls (list): A list of URLs to sort.
    Returns:
        dict: A dictionary with sorted URLs categorized by type.
        The keys are 'youtube', 'canvas', 'panopto', and 'other'.
    """
    print("Debug: Sorting URLs")
    if not urls:
        print("Debug: No URLs to sort")
        return {"youtube": [], "canvas": [], "panopto": [], "other": []}

    youtube = []
    canvas = []
    panopto = []
    other = []

    
    for u in urls:
        if not isinstance(u, str):
            print(f"Debug: Skipping non-string URL: {u}")
            continue

        lower = u.lower()

        if "youtu" in lower:
            print(f"Debug: Found YouTube URL: {u}")
            youtube.append(u)
        elif "panopto" in lower:
            print(f"Debug: Found Panopto URL: {u}")
            panopto.append(u)
        elif ("canvas" in lower) and ("files" in lower):
            print(f"Debug: Found Canvas URL: {u}")
            canvas.append(u)
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

    #sort modules and save to json
    for course in courses_ids:
        with open(f'data/courseModules/modules_{course}.json', 'r') as f:
            urls = json.load(f)
        sortedUrls = sortUrls(urls)
        with open(f'data/sortedModules/sorted_modules_{course}.json', 'w') as f:
            json.dump(sortedUrls, f, indent=4)


if __name__ == "__main__":
    main()