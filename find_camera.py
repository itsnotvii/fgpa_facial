"""Shows each camera index live so you can see which one is your webcam.

Run:  python find_camera.py
Press any key to go to the next camera, q to quit.
Then start the app with:  CAMERA_INDEX=<number> uvicorn app:app --port 8000
"""
import time

import cv2

for index in range(5):
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        cap.release()
        continue

    print(f"Camera {index}: opened, showing window (any key = next, q = quit)")
    end = time.time() + 30
    last = None
    while time.time() < end:
        ok, frame = cap.read()
        if ok:
            last = frame
            cv2.putText(frame, f"CAMERA INDEX {index}", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 255, 0), 3)
            cv2.imshow("camera", frame)
        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):
            cap.release()
            cv2.destroyAllWindows()
            raise SystemExit
        if key != 255:
            break
    if last is None:
        print(f"Camera {index}: no frames (dead/virtual device)")
    cap.release()

cv2.destroyAllWindows()
