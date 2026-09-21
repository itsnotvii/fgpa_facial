
import os
import threading
import time
from pathlib import Path

import cv2
from deepface import DeepFace
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from utils import add_embedding, best_match, load_db, save_db

MODEL_NAME = "ArcFace"
DETECTOR_BACKEND = "yunet"  # much more reliable than the Haar-based "opencv" detector
SIMILARITY_THRESHOLD = 0.40

# React (Vite) build output — run `npm run build` in frontend/ before serving.
FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"

# BGR colors for OpenCV drawing (converted from the frontend's hex palette)
COLOR_MATCH = (165, 209, 79)     # #4FD1A5 in BGR
COLOR_UNKNOWN = (91, 91, 227)    # #E35B5B in BGR


class Camera:
    """Owns the webcam, runs detection/recognition in a background thread,
    and exposes thread-safe access to the latest raw + annotated frames."""

    @staticmethod
    def _open_camera():
        """Return the first camera index that actually yields a frame.
        Some indices (virtual/Continuity cameras) open but never deliver frames.
        Set CAMERA_INDEX to force a specific one."""
        forced = os.environ.get("CAMERA_INDEX")
        candidates = [int(forced)] if forced else range(5)
        for index in candidates:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                # macOS cameras return failed/black frames until exposure settles,
                # and dead virtual cameras never leave black, so wait for a lit frame
                deadline = time.time() + 3
                while time.time() < deadline:
                    ok, frame = cap.read()
                    if ok and frame.mean() > 10:
                        return cap
                    time.sleep(0.05)
            cap.release()
        return cv2.VideoCapture(0)

    def __init__(self):
        self.cap = self._open_camera()
        self.lock = threading.Lock()
        self.raw_frame = None
        self.detections = []  # [(x, y, w, h, label, color)] from the latest recognition pass
        self.last_match = {"name": None, "score": 0.0}
        self.running = True
        threading.Thread(target=self._capture_loop, daemon=True).start()
        threading.Thread(target=self._recognize_loop, daemon=True).start()

    def _capture_loop(self):
        """Read the webcam as fast as it delivers frames so the feed stays smooth."""
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.1)
                continue
            with self.lock:
                self.raw_frame = frame

    def _recognize_loop(self):
        """Slow detect + embed + match pass; publishes boxes for the stream to draw."""
        while self.running:
            frame = self.get_raw_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            db = load_db()  # reload each pass so new enrollments show up live
            detections = []
            best_this_frame = {"name": None, "score": 0.0}

            try:
                faces = DeepFace.extract_faces(
                    img_path=frame,
                    detector_backend=DETECTOR_BACKEND,
                    enforce_detection=False,
                    align=True,
                )
            except Exception:
                faces = []

            for face in faces:
                if face.get("confidence", 1) == 0:
                    continue

                area = face["facial_area"]
                x, y, w, h = area["x"], area["y"], area["w"], area["h"]
                crop = frame[max(0, y):y + h, max(0, x):x + w]
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
                detections.append((x, y, w, h, label, color))

                if score > best_this_frame["score"]:
                    best_this_frame = {"name": name, "score": score}

            self.detections = detections
            self.last_match = best_this_frame

    def get_annotated_jpeg(self):
        """Latest raw frame with the most recent recognition boxes drawn on it."""
        frame = self.get_raw_frame()
        if frame is None:
            return None
        for x, y, w, h, label, color in self.detections:
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                frame, label, (x, max(15, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
            )
        ok, buf = cv2.imencode(".jpg", frame)
        return buf.tobytes() if ok else None

    def get_raw_frame(self):
        with self.lock:
            return None if self.raw_frame is None else self.raw_frame.copy()



app = FastAPI(title="Sentry")
if (FRONTEND_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
camera = Camera()


class EnrollRequest(BaseModel):
    name: str


@app.get("/")
def index():
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=503, detail="Frontend not built. Run `npm run build` in frontend/.")
    return FileResponse(index_file)


def _mjpeg_generator():
    while True:
        frame = camera.get_annotated_jpeg()
        if frame is not None:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        time.sleep(0.08)


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        _mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/snapshot.jpg")
def snapshot():
    """One annotated frame. The dashboard polls this, since Safari won't render
    an MJPEG stream inside an <img>."""
    frame = camera.get_annotated_jpeg()
    if frame is None:
        raise HTTPException(status_code=503, detail="Camera isn't ready yet.")
    return Response(content=frame, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@app.post("/api/enroll")
def enroll(req: EnrollRequest):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required.")

    frame = camera.get_raw_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="Camera isn't ready yet, try again in a second.")

    try:
        result = DeepFace.represent(
            img_path=frame,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=True,
        )
    except ValueError as e:
        print(f"[enroll] DeepFace error: {e!r} (frame shape {frame.shape})")
        raise HTTPException(status_code=400, detail="No face detected — center your face and try again.")

    add_embedding(name, result[0]["embedding"])
    db = load_db()
    return {"name": name, "count": len(db[name])}


@app.get("/api/roster")
def roster():
    db = load_db()
    return {name: len(embeddings) for name, embeddings in db.items()}


@app.delete("/api/roster/{name}")
def delete_person(name: str):
    db = load_db()
    if name not in db:
        raise HTTPException(status_code=404, detail="Not found.")
    del db[name]
    save_db(db)
    return {"status": "deleted"}


@app.get("/api/status")
def status():
    return {
        "enrolled_people": len(load_db()),
        "last_match": camera.last_match,
        "threshold": SIMILARITY_THRESHOLD,
    }
