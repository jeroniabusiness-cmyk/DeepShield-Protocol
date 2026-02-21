# 🛡️ DeepShield Protocol

**Real-Time AI Deepfake & Liveness Detection System**

DeepShield Protocol is a robust, real-time liveness detection system designed to defend against AI-generated spoofs and replay attacks. It utilizes **advanced photometric analysis** and **challenge-response protocols** (randomized color flashes) to measure natural facial reflections, effectively distinguishing real human presence from deepfakes or screens.

---

## ⚡ Prerequisites

Before you begin, ensure you have the following installed on your machine:
- **Python 3.x** (for the FastAPI backend)
- **Node.js / VS Code Live Server extension** (to serve the frontend)
- **Ngrok** (for securely exposing your local server to the frontend)

---

## 🛠️ Installation Steps

Follow these steps to set up the project locally:

### 1. Set up the Python Virtual Environment
Open your terminal in the project root directory and create a virtual environment (`.venv`):

```bash
python -m venv .venv
```

Activate the virtual environment:
- **Windows:**
  ```powershell
  .\.venv\Scripts\activate
  ```
- **macOS/Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 2. Install Dependencies
With the virtual environment activated, install the required Python packages:

```bash
pip install -r requirements.txt
```

*(Note: Ensure you have your `serviceAccountKey.json` for Firebase Admin placed in the root directory if you plan on using Firebase storage for background uploads).*

---

## 🚀 How to Run (Local Development)

To run the DeepShield Protocol locally, you will need to start the backend, set up an Ngrok tunnel, and serve the frontend.

### Terminal 1: Start the FastAPI Backend
Ensure your virtual environment is activated and start the FastAPI server:

```bash
uvicorn main:app --reload
```
*The backend will now be running at `http://localhost:8000` or `http://127.0.0.1:8000`.*

### Terminal 2: Start the Ngrok Tunnel
Open a new terminal session to securely expose your local backend to the internet. This is required so the frontend can successfully make requests to it without facing local browser restrictions.

```bash
ngrok http 8000
```

Once Ngrok is running, it will provide a **Forwarding URL** (e.g., `https://your-ngrok-url.ngrok-free.app`). 

👉 **Update the Frontend:**
Open `index.html` and locate the `API_URL` variable (around line 192). Replace the placeholder with your dynamically generated Ngrok URL + `/verify_liveness`:

```javascript
const API_URL = 'https://your-ngrok-url.ngrok-free.app/verify_liveness';
```

### 3. Open the Frontend
Finally, open your project in VS Code. Right-click on `index.html` and select **"Open with Live Server"**. 

Your browser will launch the TryDeepShield interface, and you can now test the Real-Time Liveness Detection!

---

## 📂 Directory Structure

Here is a brief overview of the core project structure:

```text
DeepShield/
├── main.py                  # Core FastAPI backend & reflection analysis logic
├── deepshield.js            # Client-side SDK (webcam, recording, flash sequence)
├── index.html               # Frontend UI interface
├── requirements.txt         # Python dependencies
├── serviceAccountKey.json   # (Optional) Firebase authentication credentials
├── dataset/                 # Captured biometric video data (Blackbox)
└── .venv/                   # Python virtual environment
```

---
*Developed with 💡 for enhanced biometric security.*
