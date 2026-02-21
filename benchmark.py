import requests
import os
import glob
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://127.0.0.1:8000/verify_liveness"
REAL_DIR = os.path.join("test_data", "real")
FAKE_DIR = os.path.join("test_data", "fakes")

# Challenge pattern used for testing (Must match what's in the videos)
CHALLENGE = "red,green,blue"

def test_video(file_path):
    try:
        files = {'video': open(file_path, 'rb')}
        data = {'challenge_pattern': CHALLENGE}
        response = requests.post(API_URL, files=files, data=data)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error testing {file_path}: {e}")
        return None

# Redirect print to file
import sys
sys.stdout = open("benchmark_results.txt", "w", encoding="utf-8")

def run_benchmark():
    print("🚀 Starting DeepShield Benchmark...")
    
    real_videos = glob.glob(os.path.join(REAL_DIR, "*.*"))
    fake_videos = glob.glob(os.path.join(FAKE_DIR, "*.*"))
    
    print(f"Found {len(real_videos)} Real videos and {len(fake_videos)} Fake videos.")
    
    tp = 0 # True Positive (Real detected as Real)
    tn = 0 # True Negative (Fake detected as Fake)
    fp = 0 # False Positive (Fake detected as Real)
    fn = 0 # False Negative (Real detected as Fake)
    
    # Test Real Videos
    print("\nTesting Real Videos...")
    for vid in real_videos:
        res = test_video(vid)
        if res and res['is_real']:
            print(f"✅ [PASS] {os.path.basename(vid)} -> Real (Conf: {res['confidence']})")
            tp += 1
        else:
            print(f"❌ [FAIL] {os.path.basename(vid)} -> Fake (Conf: {res.get('confidence', 0) if res else 'Err'})")
            fn += 1
            
    # Test Fake Videos
    print("\nTesting Fake Videos...")
    for vid in fake_videos:
        res = test_video(vid)
        if res and not res['is_real']:
            print(f"✅ [PASS] {os.path.basename(vid)} -> Fake")
            tn += 1
        else:
            print(f"❌ [FAIL] {os.path.basename(vid)} -> Real (Conf: {res.get('confidence', 0) if res else 'Err'})")
            fp += 1

    # Metrics
    total_real = len(real_videos)
    total_fake = len(fake_videos)
    
    accuracy = (tp + tn) / (total_real + total_fake) if (total_real + total_fake) > 0 else 0
    
    print("\n" + "="*40)
    print(f"📊 BENCHMARK RESULTS")
    print(f"Accuracy: {accuracy*100:.2f}%")
    print(f"True Positives: {tp}/{total_real}")
    print(f"True Negatives: {tn}/{total_fake}")
    print("="*40)
    
    if fn > 0:
        print("💡 Suggestion: Decrease Confidence Threshold? (Too many Reals rejected)")
    if fp > 0:
        print("💡 Suggestion: Increase Confidence Threshold? (Too many Fakes accepted)")

if __name__ == "__main__":
    if not os.path.exists(REAL_DIR) or not os.path.exists(FAKE_DIR):
        print("Error: test_data/real and test_data/fakes directories must exist.")
    else:
        run_benchmark()
