#Riley O'Shea
#University of Colorado Colorado Springs
#06/25/2025


#runs the scripts in the correct order to manage audit

import pullModules
import youtubeVideo
import embeddedVideo
import sys, json


def main():
    print("Debug: Starting audit")
    pullModules.main()
    youtubeVideo.main()
    print("Debug: Audit completed successfully")

    #run embedded video script on all courses
    with open ("data/courses_ids.json", "r") as f:
        courses = json.load(f)

    for course in courses:
        print(f"Debug: Auditing embedded videos for course {course}")
        embeddedVideo.main(course)



if __name__ == "__main__":
    main()