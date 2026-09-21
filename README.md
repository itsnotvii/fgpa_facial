# Face Recognition Take-Home

My take-home for the SCE AI x FPGA project. It's a facial recognition pipeline that runs on my laptop with a small web dashboard. The real project runs inference on a KRIA K26 board, so this is basically the laptop version of that, where I get the whole pipeline working end to end first.

## How it works

Roughly:

webcam -> find faces -> embed each face -> compare to saved people -> draw boxes -> stream to the browser

Going through it step by step:

1. **Camera.** OpenCV reads the webcam in a background thread. I did it this way so the slow face stuff doesn't freeze the web server.
2. **Detection.** DeepFace finds the faces in each frame. If it doesn't find one, the frame is skipped.
3. **Embedding.** Each face goes through ArcFace, which turns it into a list of 512 numbers. Pictures of the same person end up with similar numbers.
4. **Matching.** I compare that vector to every saved one using cosine similarity and take the best score. If it's 0.40 or higher it's a match, otherwise it says Unknown. The score always gets returned so it can be shown on screen either way.
5. **Drawing + streaming.** Green box for a match, red for unknown. The frames get sent to the browser as an MJPEG stream.
6. **Enrolling.** Type a name in the dashboard and hit Capture. The server grabs the current frame, embeds it, and saves it under that name in `embeddings.json`. The camera loop reloads the file every pass, so a new person is recognized right away without restarting.

## Why these tools

- **DeepFace + ArcFace:** the slides said to use an existing model instead of building one, and DeepFace does detection, alignment and embeddings in one library. ArcFace gives a fixed-size vector, so matching is just comparing two lists of numbers.
- **OpenCV detector:** it's fast and runs fine on a CPU. It's not the most accurate detector, but on the board this part would get swapped for AMD's optimized detection model anyway.
- **Cosine similarity:** the standard way to compare ArcFace embeddings, and it's cheap enough to keep on the server even when the board does the embedding.
- **FastAPI:** easy endpoints and it can stream responses.
- **React (Vite):** a small dashboard with the live feed, an enroll box and a list of people.
- **JSON file for storage:** no setup and I can open it and read it. A real version should use SQLite or something similar.

About the threshold: 0.40 is a cosine *similarity*, so higher means more alike. As I understand it, DeepFace's default cutoff for ArcFace is a distance of 0.68, which works out to a similarity of about 0.32. I'm using 0.40 so it's stricter. That means fewer wrong matches but sometimes it says Unknown when it shouldn't. It probably needs tuning for your lighting and camera.

## Where the FPGA comes in

The heavy part is the CNN work, meaning detection and the ArcFace embedding. That's what would move to the KRIA K26 with Vitis AI. Everything else (matching, storage, the dashboard) can stay on the server. In the code it's basically one call to swap, `DeepFace.represent`, so the board would send back embeddings instead.

## Running it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd frontend
npm install
npm run build
cd ..

uvicorn app:app --port 8000
```

Then go to http://localhost:8000. The first run downloads the ArcFace weights, so it takes a while. Your computer will ask for camera permission.

Endpoints, if you want to poke at them: `GET /video_feed`, `POST /api/enroll` with `{"name": "..."}`, `GET /api/roster`, `DELETE /api/roster/{name}`, `GET /api/status`.

## Things that aren't great yet

- No login. Anyone who can reach the server can see the feed or add and delete people, so keep it on a trusted network (Tailscale, like the slides).
- No liveness check, so a photo of someone enrolled would probably work.
- Enrolling only uses one frame and the first face it sees. A few frames from different angles would be better.
- After detection, the recognition step crops the raw frame again instead of using the already-aligned face. That probably costs some accuracy.
- The JSON store isn't safe if two requests write at the same time.
- Embeddings are biometric data and they're saved unencrypted. `embeddings.json` is in `.gitignore` so it doesn't get committed.
