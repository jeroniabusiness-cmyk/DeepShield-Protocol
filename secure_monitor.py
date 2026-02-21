import cv2
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import sys
import os

# Redirect stdout and stderr to file with UTF-8 encoding and line buffering
log_file = open("secure_monitor_log.txt", "w", encoding="utf-8", buffering=1)
sys.stdout = log_file
sys.stderr = log_file

def analyze_challenge(video_path):
    print(f"DEBUG: Secure Analysis Started on {os.path.abspath(video_path)}")
    
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    # Store deltas for each channel
    r_deltas = []
    g_deltas = []
    b_deltas = []
    
    # Track previous frame intensities
    prev_r = 0.0
    prev_g = 0.0
    prev_b = 0.0
    
    frame_count = 0
    
    print("Processing video frames...")
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        height, width, _ = frame.shape
        cx, cy = width // 2, height // 2
        
        # 50x50 ROI Center
        # Ensure ROI is valid
        y1, y2 = cy-25, cy+25
        x1, x2 = cx-25, cx+25
        
        if y1 < 0: y1 = 0
        if x1 < 0: x1 = 0
        if y2 > height: y2 = height
        if x2 > width: x2 = width
        
        roi = frame[y1:y2, x1:x2]
        
        if roi.size == 0: continue
        
        # Calculate mean intensity for B, G, R channels
        # OpenCV uses BGR ordering
        avg_b = np.mean(roi[:, :, 0])
        avg_g = np.mean(roi[:, :, 1])
        avg_r = np.mean(roi[:, :, 2])
        
        if frame_count == 0:
            # First frame, no delta
            r_deltas.append(0)
            g_deltas.append(0)
            b_deltas.append(0)
        else:
            # Calculate simple difference: Current - Previous
            # This highlights sudden changes
            r_deltas.append(avg_r - prev_r)
            g_deltas.append(avg_g - prev_g)
            b_deltas.append(avg_b - prev_b)
            
        prev_r = avg_r
        prev_g = avg_g
        prev_b = avg_b
        
        frame_count += 1
        
    cap.release()
    print(f"Finished processing {frame_count} frames.")
    
    if frame_count == 0:
        print("No frames processed.")
        return

    # Convert to numpy arrays
    r_arr = np.array(r_deltas)
    g_arr = np.array(g_deltas)
    b_arr = np.array(b_deltas)
    
    # 4. The Verdict Logic
    # We look for "Spikes" in the differential signal
    # A significant positive change means the light turned ON for that color
    # Height threshold (prominence) is key. We use 5 as a safe baseline for "sudden change"
    
    r_peaks, _ = find_peaks(r_arr, height=5, distance=10)
    g_peaks, _ = find_peaks(g_arr, height=5, distance=10)
    b_peaks, _ = find_peaks(b_arr, height=5, distance=10)
    
    print("-" * 30)
    print(f"Red Spikes detected: {len(r_peaks)}")
    print(f"Green Spikes detected: {len(g_peaks)}")
    print(f"Blue Spikes detected: {len(b_peaks)}")
    print("-" * 30)
    
    # Pass condition: All 3 colors must have triggered at least one distinct reaction
    if len(r_peaks) > 0 and len(g_peaks) > 0 and len(b_peaks) > 0:
        print("✅ COLOR REFLECTION DETECTED: Face reacted to Red, Green, and Blue flashes.")
    else:
        print("❌ INCOMPLETE RESPONSE: Did not detect clear reactions for all 3 colors.")
        print("(Note: Improve lighting or ensure screen is flashing R, G, B distinctly)")

    # 5. Plotting
    try:
        plt.figure(figsize=(10, 8))
        
        # Red Channel
        plt.subplot(3, 1, 1)
        plt.plot(r_arr, color='red', label='Red Diff')
        plt.plot(r_peaks, r_arr[r_peaks], "x", color='black')
        plt.title(f'Red Channel Differential ({len(r_peaks)} spikes)')
        plt.grid(True)
        plt.legend()
        
        # Green Channel
        plt.subplot(3, 1, 2)
        plt.plot(g_arr, color='green', label='Green Diff')
        plt.plot(g_peaks, g_arr[g_peaks], "x", color='black')
        plt.title(f'Green Channel Differential ({len(g_peaks)} spikes)')
        plt.grid(True)
        plt.legend()
        
        # Blue Channel
        plt.subplot(3, 1, 3)
        plt.plot(b_arr, color='blue', label='Blue Diff')
        plt.plot(b_peaks, b_arr[b_peaks], "x", color='black')
        plt.title(f'Blue Channel Differential ({len(b_peaks)} spikes)')
        plt.grid(True)
        plt.legend()
        
        plt.tight_layout()
        print("Saving plot to 'secure_plot.png'...")
        plt.savefig('secure_plot.png')
        print("Attempting to show plot...")
        plt.show()
        print("Plot window closed.")
        
    except Exception as e:
        print(f"Plotting failed: {e}")

if __name__ == "__main__":
    try:
        # Default to challenge.mp4
        analyze_challenge('challenge.mp4')
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    finally:
        log_file.close()
