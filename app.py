import threading
import time
import pathlib import Path

import cv2
from deepface import DeepFace
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from utils import add_embedding, best_match, load_db, save_db

MODEL_NAME = "ArcFace"
DETECTOR_BACKEND = "opencv"
SIMILARITY_THRESHOLD = 0.40

FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"

#BGR colors for openCV drawing
COLOR_MATCH = (165, 209, 79)
COLOR_UNKNOWN = (91, 91, 227)

class Camera: 

  def __init__(self):
    self.cap = cv2.VideoCapture(0)
    self.lock = threading.Lock()
    self.raw_frame = None
    self.annotated_jpeg = None
    self.last_match = {"name": None, "score": 0.0}
    self.running = True
    self.thread = threading.Thread(target=self._loop, daemon=True)
    self.thread.start()

  def _loop(self):
    while self.running:
      ok, frame = self.cap.read()
      if not ok:
        time.sleep(0.1)
        continue

      with self.lock:
        self.raw_frame = frame.copy()

      db = load_db()
      annotated = frame.copy()
      best_this_frame = {"name": None, "score": 0.0}

      try:
          faces = DeepFace.extract_faces(
            img_path=frame,
            detector_backend=DETECTOR_BACKEND,
            enforce_backend=False,
            align=True,
          )
      except Exception:
        faces = []
      