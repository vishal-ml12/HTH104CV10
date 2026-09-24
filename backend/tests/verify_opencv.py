"""
OpenCV Headless Verification Script:
1. Verifies cv2 import and prints installed version.
2. Creates a lightweight synthetic video file using cv2.VideoWriter.
3. Opens the video using cv2.VideoCapture.
4. Reads and verifies at least one frame.
5. Confirms frame extraction and dimensions.
6. Releases the video capture cleanly and deletes the temp file.
"""

import sys
import os
import tempfile
import numpy as np

def verify_opencv():
    print("=" * 60)
    print("OPENCV HEADLESS VERIFICATION SUITE")
    print("=" * 60)

    # Step 1: Import cv2
    try:
        import cv2
        print(f"[PASS] cv2 import status: SUCCESS")
        print(f"[INFO] OpenCV installed version: {cv2.__version__}")
    except Exception as e:
        print(f"[FAIL] cv2 import failed: {e}")
        sys.exit(1)

    # Step 2: Create a minimal test video
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    temp_video_path = temp_file.name
    temp_file.close()

    width, height = 320, 240
    fps = 10.0
    num_frames = 5

    try:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))
        if not writer.isOpened():
            raise RuntimeError("cv2.VideoWriter failed to open for writing.")

        for i in range(num_frames):
            frame_data = np.full((height, width, 3), (i * 40, 120, 200), dtype=np.uint8)
            cv2.putText(frame_data, f"Frame {i+1}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            writer.write(frame_data)
        writer.release()
        print(f"[PASS] Test video created successfully: {temp_video_path} ({num_frames} frames, {width}x{height})")

        # Step 3: Open the test video with cv2.VideoCapture
        cap = cv2.VideoCapture(temp_video_path)
        is_opened = cap.isOpened()
        print(f"[PASS] Video capture open status: {'OPENED' if is_opened else 'FAILED'}")
        if not is_opened:
            raise RuntimeError(f"cv2.VideoCapture could not open video: {temp_video_path}")

        # Step 4: Read at least one frame
        ret, extracted_frame = cap.read()
        print(f"[PASS] Video read status: {'SUCCESS' if ret else 'FAILED'}")
        if not ret or extracted_frame is None:
            raise RuntimeError("Failed to read frame from video.")

        # Step 5: Confirm frame extraction
        h, w, c = extracted_frame.shape
        print(f"[PASS] Frame extraction status: CONFIRMED")
        print(f"       Extracted frame dimensions: {w}x{h} with {c} color channels")
        print(f"       Frame array dtype: {extracted_frame.dtype}, min val: {extracted_frame.min()}, max val: {extracted_frame.max()}")

        # Step 6: Release video capture properly
        cap.release()
        print(f"[PASS] Video capture released: PROPERLY CLOSED")

    except Exception as ex:
        print(f"[FAIL] Runtime error during video test: {ex}")
        sys.exit(1)
    finally:
        if os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
                print(f"[INFO] Temporary test video file cleaned up.")
            except Exception:
                pass

    print("=" * 60)
    print("VERIFICATION COMPLETED: ALL CHECKS PASSED WITH ZERO ERRORS")
    print("=" * 60)

if __name__ == "__main__":
    verify_opencv()
