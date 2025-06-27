#Riley O'Shea
#University of Colorado Colorado Springs
#06/25/2025

#
import json
from youtube_transcript_api import YouTubeTranscriptApi 





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
    v = url.replace("https://www.youtube.com/watch?v=", "").replace("https://youtu.be/", "")
    try:
        srt = YouTubeTranscriptApi.get_transcript(v)
        if srt:
            print("Debug: Captions found for video")
            return True
        else:
            print("Debug: NO captions found")
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
            "type" : "youtube",
            "url" : v,
            "has_captions" : result,
        }

        with open("data/audited_videos.json", "a") as f:
           json.dump(j, f, indent=4)
           f.write("\n")


if __name__ == "__main__":
    main()