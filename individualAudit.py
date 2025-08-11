#Riley O'Shea
#University of Colorado Colorado Springs
#7/14/2025

#audits an individual course

from pullModules import getCourseModules, sortUrls
from youtubeVideo import get_youtube_videos, auditVideo
import os
import json
import sys
import sortEmbeddedVideos



def main(courseID):
    """
    args:
        courseID (str): The ID of the course to audit.
    returns:
        Results printed in 'data\audited_videos.json'
    Individual course aduit script.

    """
    #pull the modules for the course & save to json
    modules = getCourseModules(courseID)
    with open(f'data/courseModules/modules_{courseID}.json', 'w') as f:
        json.dump(modules, f, indent=4)

    #sort the modules and save to json
    sortedModules = sortUrls(modules)
    with open(f'data/sortedModules/sorted_modules_{courseID}.json', 'w') as f:
        json.dump(sortedModules, f, indent=4)

    #audit youtube videos in a single course
    videos = get_youtube_videos([courseID])
    for v in videos:
        result = auditVideo(v)

        j = {
            "type": "youtube",
            "url" : v,
            "has_captions" : result,
            "course_id": courseID,
            }

        file_path = "data/audited_videos.json"

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

        # Write back to file
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)


    # embeddedVideo.main(courseID) #run embeddedvideo.py on the courseID
    sortEmbeddedVideos.main([courseID])  # run sortEmbeddedVideos.py on the courseID



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python individualAudit.py <courseID>")
    else:
        main(sys.argv[1])