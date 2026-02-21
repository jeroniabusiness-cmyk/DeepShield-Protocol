import requests
import time
import subprocess

server = subprocess.Popen(['uvicorn', 'main:app', '--port', '8005'])
time.sleep(3)

try:
    with open('dummy.webm', 'wb') as f:
        f.write(b'dummy data')
    resp = requests.post('http://localhost:8005/verify_liveness', data={'challenge_pattern': 'red,green,blue'}, files={'video': open('dummy.webm', 'rb')})
    print("STATUS", resp.status_code)
    print("RESPONSE", resp.text)
except Exception as e:
    print("Failed to run test:", e)
finally:
    server.terminate()
