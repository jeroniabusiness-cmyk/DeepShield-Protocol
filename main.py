from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import tempfile
from physics_engine import analyze_video_challenge

app = FastAPI(title="DeepShield Headless API")

# Ensure FastAPI and CORSMiddleware are correctly set up with allow_origins=["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/verify_liveness")
async def verify_liveness(
    video_file: UploadFile = File(...), 
    flash_offset: float = Form(...)
):
    temp_file_path = None
    try:
        # 1. Save the uploaded video_file to a temporary local file
        fd, temp_file_path = tempfile.mkstemp(suffix=".webm")
        with os.fdopen(fd, 'wb') as buffer:
            shutil.copyfileobj(video_file.file, buffer)
            
        # 2. Pass this temporary file path and the flash_offset to physics_engine
        result = analyze_video_challenge(temp_file_path, flash_offset)
        
        # 4. Return the JSON result from the physics engine back to the client
        return result
        
    except Exception as e:
        return {
            "is_liveness_verified": False,
            "latency_ms": 0.0,
            "delta": 0.0,
            "message": f"Internal Server Error: {str(e)}"
        }
    finally:
        # 3. Delete the temporary video file from the server immediately after processing
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
