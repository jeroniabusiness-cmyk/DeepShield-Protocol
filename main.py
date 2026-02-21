from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import tempfile
from datetime import datetime
import cv2
import numpy as np
from scipy.signal import find_peaks
import firebase_admin
from firebase_admin import credentials, storage

app = FastAPI()

# Enable CORS (Allows Vercel frontend to make requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase Admin
storage_bucket = "YOUR_PROJECT_ID.appspot.com"
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': storage_bucket
    })
    print("Firebase Admin initialized successfully.")
except Exception as e:
    print(f"Warning: Firebase not initialized. Ensure serviceAccountKey.json exists. Error: {e}")

def analyze_reflection(video_path, challenge_pattern_str):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False, 0.0, "Video Read Error"

    # 1. Initialize Face Detector
    try:
        # Load Haar Cascade for Face Detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
    except AttributeError:
        # Fallback if cv2.data is not available
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    if face_cascade.empty():
        print("Error: Could not load Face Cascade XML.")
        return False, 0.0, "Face Detector Initialization Failed"

    # Parse Pattern
    target_colors = challenge_pattern_str.split(',') # ['red', 'green', ...]
    
    # Store deltas
    r_deltas = []
    g_deltas = []
    b_deltas = []
    
    prev_r, prev_g, prev_b = 0.0, 0.0, 0.0
    frame_count = 0
    frames_with_face = 0
    frames_with_glare = 0
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # 1. Face Detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            continue # Skip frames with no face
            
        frames_with_face += 1
        x, y, w, h = faces[0] # Use the largest/first face
        
        # 2. Extract Face ROI (Focus on center 60% to avoid background/hair)
        roi_x = x + int(w * 0.2)
        roi_y = y + int(h * 0.1)
        roi_w = int(w * 0.6)
        roi_h = int(h * 0.6)
        
        roi = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
        if roi.size == 0: continue

        # 3. Glare/Specular Reflection Detection
        # Convert to HSV to check Value (Brightness) channel
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        v_channel = hsv_roi[:, :, 2]
        
        # Check for saturated pixels (near 255) typical of screen reflections
        _, glare_mask = cv2.threshold(v_channel, 250, 255, cv2.THRESH_BINARY)
        glare_pct = cv2.countNonZero(glare_mask) / (roi_w * roi_h)
        
        if glare_pct > 0.02: # If > 2% of face ROI is blown out white
            frames_with_glare += 1
        
        # BGR
        avg_b = np.mean(roi[:, :, 0])
        avg_g = np.mean(roi[:, :, 1])
        avg_r = np.mean(roi[:, :, 2])
        
        if frame_count > 0:
            r_deltas.append(avg_r - prev_r)
            g_deltas.append(avg_g - prev_g)
            b_deltas.append(avg_b - prev_b)
        else:
            r_deltas.append(0)
            g_deltas.append(0)
            b_deltas.append(0)
            
        prev_r, prev_g, prev_b = avg_r, avg_g, avg_b
        frame_count += 1
        
    cap.release()

    # 4. Liveness Verdicts
    if frames_with_face == 0:
        return False, 0.0, "No Face Detected"
        
    glare_ratio = frames_with_glare / frames_with_face
    
    if glare_ratio > 0.1: # If > 10% of frames have glare
        return False, 0.0, "Excessive Glare Detected (Potential Replay Attack)"

    # Peak Detection (Sudden Positive Changes)
    # Thresholding is tricky with webcams (auto-exposure). 
    # Ideally, we look for relative spikes.
    
    r_arr = np.array(r_deltas)
    g_arr = np.array(g_deltas)
    b_arr = np.array(b_deltas)
    
    prominence = 5 # Adjust based on camera sensitivity
    
    r_peaks, _ = find_peaks(r_arr, height=prominence, distance=5)
    g_peaks, _ = find_peaks(g_arr, height=prominence, distance=5)
    b_peaks, _ = find_peaks(b_arr, height=prominence, distance=5)
    
    # Simple Heuristic Verification
    # We just check if the REQUIRED colors triggered a response.
    # A robust sequence match is complex due to timing drift, so we check "Presence".
    
    has_red = len(r_peaks) > 0
    has_green = len(g_peaks) > 0
    has_blue = len(b_peaks) > 0
    
    # Check if detected spikes match the UNIQUE colors in the challenge
    unique_challenges = set(target_colors)
    
    score = 0
    if 'red' in unique_challenges and has_red: score += 1
    if 'green' in unique_challenges and has_green: score += 1
    if 'blue' in unique_challenges and has_blue: score += 1
    
    match_ratio = score / len(unique_challenges)
    
    # If we matched all unique requested colors
    if match_ratio == 1.0:
        return True, 0.95, "Liveness Verified"
    elif match_ratio > 0.5:
        return True, 0.6, "Partial Match (Low Confidence)"
    else:
        return False, 0.1, "Invalid Reflection Profile (Color Mismatch)"

def upload_and_cleanup(temp_file_path: str, verdict: str, original_filename: str):
    """Background task to upload video to Firebase Storage and clean up."""
    try:
        # Check if Firebase is initialized before uploading
        if firebase_admin._apps:
            bucket = storage.bucket()
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = original_filename.split('.')[-1] if '.' in original_filename else "webm"
            # Format: REAL/20260220_154700_filename.webm
            destination_blob_name = f"{verdict}/{timestamp_str}_{verdict}.{file_ext}"
            
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(temp_file_path)
            print(f"Successfully uploaded securely to Firebase Storage: {destination_blob_name}")
        else:
            print("Firebase is not initialized. Skipping upload.")
    except Exception as e:
        print(f"Error during Firebase upload: {e}")
    finally:
        # Safely delete the local temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"Cleanup: Deleted temporary file {temp_file_path}")


@app.post("/verify_liveness")
def verify_liveness(background_tasks: BackgroundTasks, video: UploadFile = File(...), challenge_pattern: str = Form(...)):
    temp_file_path = None
    try:
        # Save File Temporarily using Python's 'tempfile' module
        fd, temp_file_path = tempfile.mkstemp(suffix=".webm")
        with os.fdopen(fd, 'wb') as buffer:
            shutil.copyfileobj(video.file, buffer)
            
        # Analyze using the temporary file path
        is_real, confidence, reason = analyze_reflection(temp_file_path, challenge_pattern)
        
        # Determine verdict for folder routing ('REAL' or 'FAKE')
        verdict = "REAL" if is_real else "FAKE"
        filename = video.filename or "video.webm"
        
        # Trigger Background Task for Firebase upload and local deletion
        background_tasks.add_task(upload_and_cleanup, temp_file_path, verdict, filename)
        
        # Respond IMMEDIATELY to the client
        return {"is_real": is_real, "confidence": confidence, "reason": reason}
        
    except Exception as e:
        # Ensure temp file is cleaned up if analysis fails before the background task is queued
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return {"error": str(e), "is_real": False, "reason": "Internal Server Error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
