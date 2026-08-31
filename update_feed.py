import json
import urllib.request

url = (
    "https://b.jw-cdn.org/apis/pub-media/"
    "GETPUBMEDIALINKS"
    "?issue=202608"
    "&output=json"
    "&pub=w"
    "&fileformat=MP3"
    "&alllangs=0"
    "&langwritten=E"
    "&txtCMSLang=E"
)

print("Contacting JW.org...")

with urllib.request.urlopen(url) as response:
    data = json.load(response)

print("Publication:", data["pubName"])
print("Issue:", data["issue"])

tracks = data["files"]["E"]["MP3"]

print()
print("Found", len(tracks), "MP3 files:")
print()

for track in tracks:
    print(track["title"])
    print(track["file"]["url"])
    print()
