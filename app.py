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

      for face in faces:
        if face.get("confidence", 1) == 0:
            continue

        area = face["facial_area"]
        x, y, w, h = area["x"], area["y"], area["w"], area["h"]
        crop = frame[max(0, y):y + h, max(0,x):x + w]
        if crop.size == 0:
            continue

        try: 
            result = DeepFace.represent(
               img_path=crop,
               model_name=MODEL_NAME,
               detector_backend="skip",
               enforce_detection=False,
            )
            embedding = result[0]["embedding"]
            name, score = best_match(embedding, db, threshold=SIMILARITY_THRESHOLD)
        except Exception:
           name, score = None, 0.0

        label = f"{name} ({score:.2f})" if name else f"Unknown ({score:.2f})"
        color = COLOR_MATCH if name else COLOR_UNKNOWN
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
           annotated, label, (x, max(0, y - 10)),
           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
        )

        if score > best_this_frame["score"]:
            best_this_frame = {"name": name, "score": score}

    self.last_match = best_this_frame
    ok2, buf = cv2.imencode(".jpg", annotated)
    if ok2:
      with self.lock:
          self.annotated_jpeg = buf.tobytes()

      