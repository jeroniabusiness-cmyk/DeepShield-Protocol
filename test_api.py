import requests
import os
import sys

# Redirect stdout to file
sys.stdout = open("api_test_log.txt", "w", encoding="utf-8")
sys.stderr = sys.stdout

API_URL = "http://127.0.0.1:8000/verify_liveness"
VIDEO_FILE = "experiment.mp4"

def test_api():
    print(f"DEBUG: Starting API Test")
    if not os.path.exists(VIDEO_FILE):
        print(f"Error: {VIDEO_FILE} not found.")
        return

    print(f"Sending {VIDEO_FILE} to {API_URL}...")
    
    # Define a challenge pattern that we KNOW exists in the video
    challenge_pattern = "red,green,blue" 
    
    files = {'video': open(VIDEO_FILE, 'rb')}
    data = {'challenge_pattern': challenge_pattern}
    
    try:
        response = requests.post(API_URL, files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(response.json())
        
        if response.status_code == 200:
            print("✅ API Test Passed!")
        else:
            print("❌ API Test Failed.")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the server running? (Run 'uvicorn main:app --reload')")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_api()
