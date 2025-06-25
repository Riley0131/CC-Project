#Riley O'Shea
#University of Colorado Colorado Springs
#06/25/2025

#
import json
from youtube_transcript_api import YouTubeTranscriptApi 





#Gets all youtube videos from user courses
def get_youtube_videos(courses):
    ytv = []
    for c in courses:
        with open(f"data/sorted_modules_{c}.json", "r") as f:
            videos = json.load(f)
        
        for item in videos["youtube"]:
            if "youtube.com/watch?v=" in item or "youtu.be/" in item:
                ytv.append(item)


    return ytv

#audit a single video to see if it has captions
def auditVideo(url):
    v = url.replace("https://www.youtube.com/watch?v=", "").replace("https://youtu.be/", "")
    try:
        srt = YouTubeTranscriptApi.get_transcript(v)
        if srt:
            return True
        else:
            return False

    except Exception as e:
        # print(f"Error fetching transcript for {url}: {e}")
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
           json.dump(j, f)
           f.write("\n")


if __name__ == "__main__":
    main()