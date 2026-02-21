import cv2
import numpy as np
import matplotlib
matplotlib.use('TkAgg') # Use TkAgg for window display if possible, or swap to Agg if needed
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, square
import sys

# Redirect stdout and stderr to file with UTF-8 encoding and line buffering
log_file = open("monitor_log.txt", "w", encoding="utf-8", buffering=1)
sys.stdout = log_file
sys.stderr = log_file

def analyze_liveness(video_path):
    print("DEBUG: Analysis started (Cross-Correlation Method)")
    
    # 1. Signal Extraction
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    raw_intensities = []
    frame_count = 0

    print("Processing video frames...")
    while True:
        ret, frame = cap.read()
        if not ret: break

        height, width, _ = frame.shape
        cx, cy = width // 2, height // 2
        # 50x50 ROI
        roi = frame[cy-25:cy+25, cx-25:cx+25]
        
        if roi.size == 0: continue

        # Green channel average
        avg_green = np.mean(roi[:, :, 1])
        raw_intensities.append(avg_green)
        frame_count += 1

    cap.release()
    print(f"Finished processing {frame_count} frames.")

    if not raw_intensities:
        print("No frames processed.")
        return

    # Convert to array
    signal = np.array(raw_intensities)

    # Normalize Signal (0 to 1)
    if np.max(signal) - np.min(signal) == 0:
        print("Error: Signal is flat (no variation).")
        return
    
    norm_signal = (signal - np.min(signal)) / (np.max(signal) - np.min(signal))

    # 2. Frequency Estimation (The "Ground Truth" Period)
    # Find peaks to estimate period
    peaks, _ = find_peaks(norm_signal, prominence=0.2, distance=10) # Prominence 0.2 on normalized signal
    
    if len(peaks) < 2:
        print("❌ FAILED: Not enough peaks to estimate frequency. (Static or erratic lighting)")
        return

    # Average distance between peaks = Period (in frames)
    peak_diffs = np.diff(peaks)
    avg_period = np.mean(peak_diffs)
    print(f"Estimated Flash Period: {avg_period:.2f} frames")

    # 3. Reference Signal Creation
    # Create a synthetic square wave with the estimated period
    # We create it for the same duration as the video
    t = np.arange(len(norm_signal))
    # 2*pi*f*t -> f = 1/period
    ref_signal = 0.5 * (square(2 * np.pi * (1/avg_period) * t) + 1) # Shift to 0-1 range

    # 4. The Physics Test (Cross-Correlation)
    # Center signals around 0 for correlation
    sig_centered = norm_signal - np.mean(norm_signal)
    ref_centered = ref_signal - np.mean(ref_signal)

    # Compute Cross-Correlation
    correlation = np.correlate(sig_centered, ref_centered, mode='full')
    
    # Normalize Correlation Coefficient (-1 to 1)
    # Coeff = dot(a,b) / (norm(a) * norm(b))
    norm_factor = np.sqrt(np.sum(sig_centered**2) * np.sum(ref_centered**2))
    if norm_factor == 0:
        max_corr = 0
    else:
        max_corr = np.max(correlation) / norm_factor

    # Lag/Shift calculation (Index of max correlation)
    lag_index = np.argmax(correlation) - (len(norm_signal) - 1)
    
    # Create Aligned Reference for Plotting
    # We shift the reference signal by 'lag_index' to visually match the face signal
    aligned_ref = np.roll(ref_signal, lag_index)

    print("-" * 30)
    print(f"Max Correlation Coefficient: {max_corr:.4f}")
    print(f"Optimal Lag: {lag_index} frames")
    print("-" * 30)

    # 5. Final Verdict
    if max_corr > 0.5:
        print(f"✅ LIVENESS CONFIRMED: High Correlation Detected (Score: {max_corr:.2f})")
    else:
        print("❌ SPOOF DETECTED: Signal does not match Screen Pattern")

    # 6. Plotting
    try:
        plt.figure(figsize=(12, 6))
        
        plt.subplot(2, 1, 1)
        plt.plot(t, norm_signal, 'b-', label='Normalized Face Signal (Green Ch)')
        plt.plot(t, aligned_ref, 'orange', linestyle='--', label='Aligned Synthetic Reference')
        plt.title(f'Liveness Check: Correlation Score {max_corr:.2f}')
        plt.legend(loc='upper right')
        plt.grid(True)
        
        plt.subplot(2, 1, 2)
        lags = np.arange(-len(norm_signal) + 1, len(norm_signal))
        plt.plot(lags, correlation / norm_factor, 'k-', label='Cross-Correlation')
        plt.title('Cross-Correlation vs Lag')
        plt.xlabel('Lag (Frames)')
        plt.ylabel('Correlation Coeff')
        plt.grid(True)
        plt.tight_layout()

        print("Saving plot to 'result_plot.png'...")
        plt.savefig('result_plot.png')
        print("Attempting to show plot...")
        plt.show()
        print("Plot window closed.")
    except Exception as e:
        print(f"Plotting failed: {e}")

if __name__ == "__main__":
    try:
        analyze_liveness('experiment.mp4')
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    finally:
        log_file.close() # Ensure file is saved
