import requests
import os
import time

# Ensure server is running before running this script
url = "http://127.0.0.1:8000/verify_liveness"
video_path = "e:/life changing project/challenge.mp4"
challenge = "red,green,blue"

if not os.path.exists(video_path):
    # create a dummy video file if it doesn't exist just for testing
    with open("temp_dummy.mp4", "wb") as f:
        f.write(b"dummy video content")
    video_path = "temp_dummy.mp4"

files = {'video': open(video_path, 'rb')}
data = {'challenge_pattern': challenge}

print(f"Sending request to {url}...")
try:
    response = requests.post(url, files=files, data=data)
    print("Status Code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", e)

# Check if file was created in dataset/collected_videos
dataset_dir = "dataset/collected_videos"
if os.path.exists(dataset_dir):
    files = os.listdir(dataset_dir)
    print("\nFiles in dataset/collected_videos:")
    for f in files:
        print(f)
else:
    print("\ndataset/collected_videos directory not found!")
