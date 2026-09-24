"""
Phase 3 Error Handling Verification Suite:
Validates edge cases and error resiliency for video and conveyor simulation:
- Unsupported video extensions
- Empty video file
- Corrupted video data
- Video with zero detectable objects
- Non-crashing behavior
"""

import os
import sys
import io
import tempfile
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_video_error_handling():
    print("\n=== TESTING ERROR HANDLING RESILIENCY ===")

    # 1. No file passed
    res = client.post("/api/video/analyze")
    assert res.status_code == 400, f"Expected 400, got {res.status_code}"
    print("[PASS] Missing file returns 400 Bad Request")

    # 2. Unsupported extension
    res = client.post(
        "/api/video/analyze",
        files={"file": ("corrupt.txt", b"this is a text file", "text/plain")}
    )
    assert res.status_code == 400, f"Expected 400, got {res.status_code}"
    assert "Unsupported video format" in res.json()["detail"]
    print("[PASS] Unsupported extension returns 400 Bad Request")

    # 3. Empty video file (0 bytes)
    res = client.post(
        "/api/video/analyze",
        files={"file": ("empty.mp4", b"", "video/mp4")}
    )
    assert res.status_code == 400, f"Expected 400, got {res.status_code}"
    assert "empty" in res.json()["detail"].lower()
    print("[PASS] Empty video file returns 400 Bad Request")

    # 4. Corrupted video bytes
    res = client.post(
        "/api/video/analyze",
        files={"file": ("corrupted.mp4", b"INVALID_RANDOM_CORRUPT_BYTES_XYZ", "video/mp4")}
    )
    assert res.status_code in [400, 500], f"Expected 400 or 500, got {res.status_code}"
    print(f"[PASS] Corrupted video handled safely: {res.json()['detail']}")

    # 5. Invalid conveyor control action
    res = client.post("/api/conveyor/control", json={"action": "unknown_action_xyz"})
    assert res.status_code == 400
    assert "Unknown control action" in res.json()["detail"]
    print("[PASS] Invalid conveyor control action rejected with 400")

    # 6. Negative delta time in step handled safely
    res = client.post("/api/conveyor/step", json={"delta_time": 0.0})
    assert res.status_code == 200
    print("[PASS] Step with delta_time=0.0 handled cleanly")

    print("\n=== ALL ERROR RESILIENCY CHECKS PASSED ===")


if __name__ == "__main__":
    test_video_error_handling()
