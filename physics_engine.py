import cv2
import numpy as np
import os

def analyze_video_challenge(video_path: str, flash_start_time_offset: float) -> dict:
    """
    Headless Physics Engine for Liveness Detection (Phase 3).
    Extracts Forehead ROI using Haar Cascades, calculates the Dynamic Baseline, Red Peak, Delta, and Latency.
    """
    if not os.path.exists(video_path):
        return {
            "is_liveness_verified": False,
            "latency_ms": 0.0,
            "delta": 0.0,
            "message": "Video file not found."
        }

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {
            "is_liveness_verified": False,
            "latency_ms": 0.0,
            "delta": 0.0,
            "message": "Error opening video file."
        }
        
    # Get FPS to calculate accurate timestamps if CAP_PROP_POS_MSEC fails
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or np.isnan(fps):
        fps = 30.0

    # Load Haar cascade for frontal face
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
    except AttributeError:
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    if face_cascade.empty():
        cap.release()
        return {
            "is_liveness_verified": False,
            "latency_ms": 0.0,
            "delta": 0.0,
            "message": "Face Detector Initialization Failed"
        }

    red_intensities = []
    timestamps_ms = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        current_time_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
        if current_time_ms == 0 and frame_count > 0:
            current_time_ms = (frame_count / fps) * 1000.0

        # Face Detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
        
        red_val = 0.0
        if len(faces) > 0:
            # Sort by area to get the largest face
            faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
            x, y, w, h = faces[0]
            
            # Extract Forehead ROI (top 30% of the face box, center 60% horizontally to avoid hair/background)
            fh_y = y
            fh_h = int(h * 0.3)
            fh_x = x + int(w * 0.2)
            fh_w = int(w * 0.6)
            
            roi = frame[fh_y:fh_y+fh_h, fh_x:fh_x+fh_w]
            if roi.size > 0:
                # Mean red intensity (OpenCV uses BGR format, so Red is index 2)
                red_val = np.mean(roi[:, :, 2])
        
        red_intensities.append(red_val)
        timestamps_ms.append(current_time_ms)
        frame_count += 1
        
    cap.release()
    
    if len(red_intensities) == 0:
        return {
            "is_liveness_verified": False,
            "latency_ms": 0.0,
            "delta": 0.0,
            "message": "No frames processed."
        }

    red_arr = np.array(red_intensities)
    time_arr = np.array(timestamps_ms)
    
    # 1. Dynamic Baseline Calculation (Average red intensity BEFORE flash)
    pre_flash_mask = time_arr < flash_start_time_offset
    if np.any(pre_flash_mask):
        dynamic_baseline = np.mean(red_arr[pre_flash_mask])
    else:
        # Fallback: average of first 10% frames if flash starts very early (or missing offset)
        dynamic_baseline = np.mean(red_arr[:max(1, len(red_arr)//10)])
        
    # 2. Red Peak Calculation (Max red intensity AFTER flash)
    post_flash_mask = time_arr >= flash_start_time_offset
    if not np.any(post_flash_mask):
        return {
            "is_liveness_verified": False,
            "latency_ms": 0.0,
            "delta": 0.0,
            "message": "No frames found after flash offset."
        }
        
    post_flash_intensities = red_arr[post_flash_mask]
    post_flash_timestamps = time_arr[post_flash_mask]
    
    max_idx = np.argmax(post_flash_intensities)
    red_peak = post_flash_intensities[max_idx]
    peak_timestamp = post_flash_timestamps[max_idx]
    
    # 3. Delta
    delta = red_peak - dynamic_baseline
    
    # 4. Latency Calculation (Time between flash start and peak response)
    latency_ms = peak_timestamp - flash_start_time_offset
    
    # Verification conditions (Robust defaults for living tissue response to flash)
    delta_threshold = 3.0 # Minimum recognizable increase in red intensity
    max_latency = 1200.0  # Maximum acceptable physiological and network delay in milliseconds
    
    is_liveness_verified = bool((delta > delta_threshold) and (0 <= latency_ms <= max_latency))
    
    message = "Liveness Verified" if is_liveness_verified else "Spoof Detected or No Flash Response"

    return {
        "is_liveness_verified": is_liveness_verified,
        "latency_ms": float(latency_ms),
        "delta": float(delta),
        "message": message
    }

if __name__ == "__main__":
    # For local debugging
    pass
