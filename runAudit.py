#Riley O'Shea
#University of Colorado Colorado Springs
#06/25/2025


#runs the scripts in the correct order to manage audit

import pullModules
import youtubeVideo
import embeddedVideo
import sys, json

def sortEmbedNeed(courses):
    embeddedmodulesToAudit = []
    for course in courses:
        if "embeddedVideos" in course:
            for module in course["embeddedVideos"]:
                if "videoId" in module:
                    embeddedmodulesToAudit.append(module)


def main():
    print("Debug: Starting audit")
    pullModules.main()
    youtubeVideo.main()
    print("Debug: Audit completed successfully")

    #run embedded video script on all courses
    with open ("data/courses_ids.json", "r") as f:
        courses = json.load(f)

    embeddedVideosToAudit = sortEmbedNeed(courses)
    for video in embeddedVideosToAudit:
        print(video)



if __name__ == "__main__":
    main()