#Riley O'Shea
#University of Colorado Colorado Springs
#7/7/25

#retrieves links to panopto videos and performs audit on panopto links
import json
from config.panoptoKey import Client_ID, Client_Secret
import requests
from urllib.parse import urljoin

token_url = "https://uccs1.hosted.panopto.com/Panopto/oauth2/connect/token"
token_data = {
    "grant_type": "client_credentials",
    "scope" : "api"
}

response = requests.post(token_url, data=token_data, auth=(Client_ID, Client_Secret))

if response.status_code == 200:
    access_token = response.json()["access_token"]
    print("Debug: Access Token Obtained")
else:
    print("Debug: Failed to get access token:", response.status_code, response.text)

#gets all panopto links in course modules
def getPanoptoVideos(courses):
    print("Debug: Fetching Panopto videos from courses")
    pvd = []
    for c in courses:
        with open(f"data/sortedModules/sorted_modules_{c}.json","r") as f:
            videos = json.load(f)
        if "panopto" not in videos or not videos["panopto"]:
            print(f"Debug: No Panopto videos in course {c}")
            continue
        

        for item in videos["panopto"]:
            if "panopto" in item:
                pvd.append(item)
                print("Debug: Found Panopto Video")
            else:
                print("Debug: Skipping non Panopto URL")
                continue
    return pvd

def auditPanoptoVideo(video):
    print("Debug: Auditing Panopto video ")

def main():
    with open(f"data/courses_ids.json", "r") as f:
        courses = json.load(f)
    
    videos = getPanoptoVideos(courses)
    for v in videos:
        print(v)
    


if __name__ == "__main__":
    main()