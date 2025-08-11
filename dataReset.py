#Riley O'Shea
#University of Colorado Colorado Springs
#7/7/25

#WARNING: This will erase all data collected by the program, do not run unless this is the intended function.
# Deletes existing data files in the 'data' directory for resetting audit results.

import os
import glob

def resetDataFiles():
    data_folder = "data"
    
    #ensures that the data folder exists
    if not os.path.isdir(data_folder):
        print(f"No '{data_folder}' folder found. Nothing to delete.")
        return

    #finds all .json files in the data folder and its subfolders
    json_files = glob.glob("data/*.json") + glob.glob("data/courseModules/*.json") + glob.glob("data/sortedModules/*.json")

    #case where no .json files are found
    if not json_files:
        print("No .json files found to delete.")
        return

    #removes .json files found
    for file in json_files:
        try:
            os.remove(file)
            print(f"Removed {file}")
        except Exception as e:
            print(f"Failed to delete {file}: {e}")

def main():
    resetDataFiles()

if __name__ == "__main__":
    main()
