# Sentry — Facial Recognition Pipeline

End-to-end facial detection and recognition on a laptop webcam, with a live web dashboard. Built as the SCE "AI x FPGA" take-home. The long-term target is running the inference stage on an AMD KRIA K26 SOM (Vitis AI); this repo is the laptop prototype of that pipeline.

## Pipeline

```
webcam ──> face detection ──> alignment/crop ──> embedding (ArcFace) ──> cosine match vs. enrolled DB ──> annotated MJPEG ──> React dashboard
```

1. **Capture** — `Camera` (in `app.py`) owns the webcam (OpenCV `VideoCapture`) and runs a background thread so slow inference never blocks the HTTP server.
2. **Detect** — `DeepFace.extract_faces` with the OpenCV detector returns face boxes and aligned crops. Frames with no face (confidence 0) are skipped.
3. **Embed** — each face is turned into a 512-dim ArcFace vector via `DeepFace.represent`. Two photos of the same person land close together in this space.
4. **Match** — `utils.best_match` computes cosine similarity against every stored embedding and takes the best. At or above the threshold (0.40) it is a match; otherwise "Unknown". The score is always returned so the UI can display it.
5. **Annotate + stream** — boxes and labels are drawn (green = match, red = unknown), JPEG-encoded, and served as MJPEG at `/video_feed`.
6. **Enroll** — `POST /api/enroll` grabs the current frame, embeds the face, and appends it to that person's entry in `embeddings.json`. The camera loop reloads the DB each pass, so new people are recognized live.

## Tool choices and why

| Tool | Why |
|---|---|
| **DeepFace** | One API for detection, alignment, and embedding; the course slides suggest existing models over building from scratch. |
| **ArcFace** | Strong accuracy for its size, and a fixed-size embedding makes matching a simple vector comparison. |
| **OpenCV detector** | Fast and dependency-light on CPU. Weaker than CNN detectors; the FPGA phase would swap in an optimized AMD model. |
| **Cosine similarity** | Standard for ArcFace embeddings; cheap enough to run on the server even on the FPGA-based design. |
| **FastAPI** | Simple typed endpoints plus streaming responses. |
| **React (Vite)** | Lightweight dashboard: live feed, enroll form, roster, status. |
| **JSON file store** | Zero setup and human-readable. A real deployment would use SQLite or a vector store. |

### Threshold

`SIMILARITY_THRESHOLD = 0.40` is a cosine *similarity* (higher = more alike). DeepFace's own ArcFace cosine cutoff is a distance of 0.68 (similarity ≈ 0.32), so 0.40 is deliberately stricter: fewer false accepts, at the cost of more false "Unknown" results. Tune it on your own lighting and camera.

## Mapping to the FPGA (KRIA K26)

- **Moves to the board:** detection and ArcFace embedding inference (the CNN work), via Vitis AI.
- **Stays on the server:** cosine matching, enrollment storage, and the dashboard. The board would return embeddings, and `DeepFace.represent` is the single call to replace.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cd frontend && npm install && npm run build && cd ..

uvicorn app:app --port 8000
```

Open http://localhost:8000. The first run downloads the ArcFace weights, so it is slow. Allow camera access when prompted.

API: `GET /video_feed`, `POST /api/enroll {"name": "..."}`, `GET /api/roster`, `DELETE /api/roster/{name}`, `GET /api/status`.

## Known limitations

- No authentication: anyone who can reach the server can view the feed or enroll/delete people. Run it on a trusted network (e.g. Tailscale).
- No liveness detection: a photo of an enrolled person can match.
- Enrollment uses a single frame and the first detected face. Several varied frames would be more robust.
- The recognition step re-crops the raw frame instead of reusing the aligned crop from detection, which likely costs some accuracy.
- The JSON store is not safe against concurrent read-modify-write from multiple requests.
- Embeddings are biometric data stored unencrypted; `embeddings.json` is git-ignored.
