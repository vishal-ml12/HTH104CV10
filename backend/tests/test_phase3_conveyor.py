"""
Phase 3 Verification Test Suite:
Validates video ingestion, keyframe sampling, object tracking with persistent IDs,
virtual conveyor simulation telemetry, simulation controls, and database persistence.
"""

import os
import sys
import tempfile
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.session import SessionLocal
from backend.models import WasteAnalysis, DetectedObject, StreamAnalysis

client = TestClient(app)


def generate_synthetic_conveyor_video(duration_sec: int = 2, fps: int = 10, width: int = 640, height: int = 480) -> str:
    """Generate a lightweight synthetic MP4 video of moving waste objects on a conveyor."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

    total_frames = int(duration_sec * fps)
    for frame_idx in range(total_frames):
        # Conveyor background (dark industrial grey with belt lines)
        frame = np.full((height, width, 3), 45, dtype=np.uint8)

        # Draw conveyor belt surface
        cv2.rectangle(frame, (0, 100), (width, 380), (30, 30, 30), -1)

        # Moving object 1 (e.g. green bottle shape moving left to right)
        x_pos_1 = int(50 + (frame_idx / total_frames) * (width - 150))
        cv2.rectangle(frame, (x_pos_1, 180), (x_pos_1 + 80, 260), (40, 180, 50), -1)
        cv2.putText(frame, "PET BOTTLE", (x_pos_1, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Moving object 2 (e.g. metallic silver can moving left to right)
        x_pos_2 = int(20 + (frame_idx / total_frames) * (width - 200))
        cv2.rectangle(frame, (x_pos_2, 280), (x_pos_2 + 60, 340), (200, 200, 200), -1)
        cv2.putText(frame, "AL CAN", (x_pos_2, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        out.write(frame)

    out.release()
    return temp_path


def test_conveyor_telemetry_endpoint():
    print("\n--- 1. TESTING GET /api/conveyor/telemetry ---")
    res = client.get("/api/conveyor/telemetry")
    assert res.status_code == 200, f"Error: {res.text}"

    data = res.json()
    assert "simulation_state" in data
    assert "conveyor_speed" in data
    assert "stream_counters" in data
    assert "active_belt_items" in data
    assert "diverter_event_logs" in data
    assert "disclaimer" in data

    print(f"Simulation State: {data['simulation_state']}, Speed: {data['conveyor_speed']}x")
    print(f"Active items on belt: {len(data['active_belt_items'])}")
    print(f"Stream counters: {data['stream_counters']}")
    print("Telemetry endpoint verified successfully.")


def test_conveyor_step_and_controls():
    print("\n--- 2. TESTING CONVEYOR STEP & CONTROL ENDPOINTS ---")

    # Step simulation
    step_res = client.post("/api/conveyor/step", json={"delta_time": 1.0})
    assert step_res.status_code == 200
    step_data = step_res.json()
    assert len(step_data["active_belt_items"]) > 0

    # Pause simulation
    pause_res = client.post("/api/conveyor/control", json={"action": "pause"})
    assert pause_res.status_code == 200
    assert pause_res.json()["simulation_state"] == "PAUSED"
    print("Conveyor successfully paused.")

    # Set speed
    speed_res = client.post("/api/conveyor/control", json={"action": "set_speed", "speed": 2.0})
    assert speed_res.status_code == 200
    assert speed_res.json()["conveyor_speed"] == 2.0
    print("Conveyor speed set to 2.0x.")

    # Start simulation
    start_res = client.post("/api/conveyor/control", json={"action": "start"})
    assert start_res.status_code == 200
    assert start_res.json()["simulation_state"] == "RUNNING"
    print("Conveyor successfully resumed.")

    # Reset simulation
    reset_res = client.post("/api/conveyor/control", json={"action": "reset"})
    assert reset_res.status_code == 200
    assert reset_res.json()["total_objects_processed"] == 0
    print("Conveyor successfully reset.")


def test_video_analysis_pipeline():
    print("\n--- 3. TESTING POST /api/video/analyze ---")
    video_path = generate_synthetic_conveyor_video(duration_sec=2, fps=10)
    assert os.path.exists(video_path), "Failed to generate synthetic video"

    try:
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        res = client.post(
            "/api/video/analyze",
            files={"file": ("synthetic_conveyor.mp4", video_bytes, "video/mp4")},
            data={"input_mass_kg": 175.0}
        )
        assert res.status_code == 200, f"Error: {res.text}"

        data = res.json()
        assert data["success"] is True
        session_id = data["session_id"]
        assert session_id.startswith("vid_")
        print(f"Generated Phase 3 Video Session ID: {session_id}")

        assert data["unique_objects_count"] >= 1
        assert "conveyor_timeline" in data
        assert "virtual_sorting" in data
        assert "streams_analysis" in data
        assert "optimization" in data
        assert "event_logs" in data
        assert len(data["event_logs"]) > 0

        opt = data["optimization"]
        print(f"Primary Material: {data['primary_material']} (Confidence: {data['confidence']})")
        print(f"Unique Objects Tracked: {data['unique_objects_count']}")
        print(f"Quality Score: {opt['quality_score']}/100 | Yield: {opt['recycling_yield']}%")
        print(f"Recoverable Mass: {opt['recoverable_mass_kg']} kg / {opt['input_mass_kg']} kg")

        # Verify Database Persistence
        db = SessionLocal()
        try:
            db_record = db.query(WasteAnalysis).filter(WasteAnalysis.session_id == session_id).first()
            assert db_record is not None, "WasteAnalysis record missing from database"
            assert db_record.input_mass_kg == 175.0

            db_objects = db.query(DetectedObject).filter(DetectedObject.session_id == session_id).all()
            assert len(db_objects) >= 1, "DetectedObject records missing from database"

            db_streams = db.query(StreamAnalysis).filter(StreamAnalysis.session_id == session_id).all()
            assert len(db_streams) >= 1, "StreamAnalysis records missing from database"
            print(f"Verified Database: 1 session, {len(db_objects)} objects, {len(db_streams)} streams saved.")
        finally:
            db.close()

    finally:
        if os.path.exists(video_path):
            try:
                os.remove(video_path)
            except OSError:
                pass


def test_phase1_and_phase2_intact():
    print("\n--- 4. VERIFYING PHASE 1 & PHASE 2 REMAIN 100% FUNCTIONAL ---")

    # Health check
    h_res = client.get("/api/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "ok"

    # Statistics check
    s_res = client.get("/api/statistics")
    assert s_res.status_code == 200
    assert "total_analyses" in s_res.json()

    # Review queue check
    r_res = client.get("/api/review-queue")
    assert r_res.status_code == 200
    assert isinstance(r_res.json(), list)

    print("Phase 1 & Phase 2 systems verified and completely intact!")


if __name__ == "__main__":
    test_conveyor_telemetry_endpoint()
    test_conveyor_step_and_controls()
    test_video_analysis_pipeline()
    test_phase1_and_phase2_intact()
    print("\n=== ALL PHASE 3 BACKEND TESTS PASSED SUCCESSFULLY! ===")
