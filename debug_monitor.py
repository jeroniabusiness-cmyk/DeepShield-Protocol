import sys
import os
print("DEBUG: Script started", flush=True)

try:
    import cv2
    print("DEBUG: cv2 imported", flush=True)
except Exception as e:
    print(f"DEBUG: cv2 import failed: {e}", flush=True)

try:
    import matplotlib
    print("DEBUG: matplotlib imported", flush=True)
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    print("DEBUG: matplotlib.pyplot imported (Agg backend)", flush=True)
except Exception as e:
    print(f"DEBUG: matplotlib import failed: {e}", flush=True)

try:
    from scipy.signal import find_peaks
    print("DEBUG: scipy.signal.find_peaks imported", flush=True)
except Exception as e:
    print(f"DEBUG: scipy import failed: {e}", flush=True)

print("DEBUG: Script finished", flush=True)
