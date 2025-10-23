#Riley O'Shea
#University of Colorado Colorado Springs
#06/25/2025


#runs the scripts in the correct order to manage audit

import pullModules
import youtubeVideo
import panoptoVideo
import sortEmbeddedVideos
import sys, json
    

def main():
    """Main function to run a complete audit."""
    print("Debug: Starting audit")
    pullModules.main()
    youtubeVideo.main()
    panoptoVideo.main()
    print("Debug: Audit completed successfully")

    #create a container for all course IDs
    courseIDs = []
    #load course IDs from the modules json file
    with open('data/courses_ids.json', 'r') as f:
        try:
            #fill courseIDs with the list of ids from the json file
            courseIDs = json.load(f)
        except json.JSONDecodeError:
            #throw an error and exit if the json file is invalid
            print("Error: Could not decode JSON from course_ids.json")
            sys.exit(1)

    #run embedded video audit on list of courseIDs
    sortEmbeddedVideos.main(courseIDs)
   


if __name__ == "__main__":
    main()
