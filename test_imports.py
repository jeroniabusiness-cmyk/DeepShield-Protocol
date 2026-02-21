import sys
import traceback

with open("import_test_log.txt", "w") as f:
    f.write("Starting import test...\n")
    try:
        import cv2
        f.write("CV2 OK\n")
    except Exception:
        f.write("CV2 FAILED\n")
        f.write(traceback.format_exc())

    try:
        import numpy
        f.write("Numpy OK\n")
    except Exception:
        f.write("Numpy FAILED\n")
        f.write(traceback.format_exc())

    try:
        import fastapi
        f.write("FastAPI OK\n")
    except Exception:
        f.write("FastAPI FAILED\n")
        f.write(traceback.format_exc())
        
    try:
        import uvicorn
        f.write("Uvicorn OK\n")
    except Exception:
        f.write("Uvicorn FAILED\n")
        f.write(traceback.format_exc())

    f.write("Test Complete.\n")
