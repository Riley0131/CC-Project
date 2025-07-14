#Riley O'Shea
#University of Colorado Colorado Springs
#06/25/2025

#
import json
from youtube_transcript_api import YouTubeTranscriptApi 
import time
import os


def normalize_youtube_url(url):
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    elif "youtube.com/watch" in url:
        return url
    else:
        return None  # or raise an error if you'd rather be strict


#Gets all youtube videos from user courses
def get_youtube_videos(courses):
    print("Debug: Fetching YouTube videos from courses")
    ytv = []
    for c in courses:
        with open(f"data/sortedModules/sorted_modules_{c}.json", "r") as f:
            videos = json.load(f)
        #running into error because file doesn't have any thing in it so when it reads null it fails.
        if not videos or "youtube" not in videos:
            print(f"Debug: No YouTube videos found in course {c}")
            continue
        
        for item in videos["youtube"]:
            if "youtube.com/watch?v=" in item or "youtu.be/" in item:
                ytv.append(item)
                print("Debug: Found YouTube video:")
            else:
                print("Debug: Skipping non-YouTube URL:")
                continue


    return ytv

#audit a single video to see if it has captions
def auditVideo(url):
    time.sleep(5)
    v = url.replace("https://www.youtube.com/watch?v=", "").replace("https://youtu.be/", "")
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(v)

        if transcript:
            print(f"Debug: Video {url} has captions.")
            return True
        else:
            print(f"Debug: Video {url} does not have captions.")
            return False
        
    except Exception as e:
        print(f"Error fetching transcript for {url}: {e}")
        return False



def main():
    with open(f"data/courses_ids.json", "r") as f:
        courses = json.load(f)


    videos = get_youtube_videos(courses)
    for v in videos:
        #print(v)
        result = auditVideo(v)
        #print(result)

        j = {
            "type": "youtube",
            "url": v,
            "has_captions": result,
        }

        file_path = "data/audited_videos.json"

        # Load existing data or initialize an empty list
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


if __name__ == "__main__":
    main()