# Closed Captioning Audit
This tool is designed for auditing Canvas courses to ensure accessibility compliance by giving the user a detailed list of videos from a single course or multiple courses and if they contain captions.  
Developed by: Riley O'Shea  
Email: roshea@uccs.edu  
University of Colorado Colorado Springs

# Warning / Disclaimer
This program is still under development and may have issues, please use caution when using audit results. For known issues and bugs visit: https://github.com/Riley0131/CC-Project/issues  
This tool does not accept videos with "burned in captions" (captions that are an overlay in the video not a true caption file) they will not be identified as having captions

# Supported Video Types
Youtube Videos (public videos only)  
Embedded Canvas Videos (published)  

## Setup
For some accounts the canvas videos will use the account signed into the computer to audit videos, if the account that you are signed in with doesn't have access to the correct course it will result in a negative value for all embedded videos  
Run the program, on the first time running you will need to enter a canvas API key see [Obtaining Canvas API Key](#obtaining-canvas-api-key) section for details.  

### Obtaining Canvas API Key
1. log into the canvas account which is enrolled in the audited courses
2. Select the "Account" page on the left
3. Select "Settings"
4. Under "Approved Integrations" Select the "New Access Token" Button
5. Enter a purpose eg. "Closed Captioning Auditor" you can add an expiration or leave this empty
6. Copy the "Token" (do not share this with anyone sharing can result in data breaches and information being stolen)  
Note: once you close the access token page it is gone if you lose it or delete it it cannot be found again.