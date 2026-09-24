import os
import sys
import io
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.session import SessionLocal
from backend.models import WasteAnalysis, DetectedObject

client = TestClient(app)


def test_full_virtual_sorting_pipeline():
    print("--- 1. TESTING POST /api/analyze WITH REAL PLASTIC BOTTLE ---")
    bottle_path = r"C:\Users\sysadmin\Pictures\empty-green-used-water-bottle-recycling-145080483.webp"
    assert os.path.exists(bottle_path), f"Bottle image not found at {bottle_path}"

    with open(bottle_path, "rb") as f:
        file_bytes = f.read()

    res = client.post("/api/analyze", files={"file": ("green_bottle.webp", file_bytes, "image/webp")})
    assert res.status_code == 200, f"Error: {res.text}"

    data = res.json()
    assert data["success"] is True
    assert "session_id" in data
    session_id = data["session_id"]
    print(f"Generated Session ID: {session_id}")

    analysis = data["analysis"]
    assert "detected_objects" in analysis
    detected_objs = analysis["detected_objects"]
    print(f"Detected Objects Count: {len(detected_objs)}")
    for obj in detected_objs:
        print(f"  Object ID: {obj['object_id']} | Material: {obj['material']} | Conf: {obj['confidence']} | Stream: {obj['stream']} | Status: {obj['status']}")
        assert "bbox" in obj
        assert "normalized" in obj["bbox"]

    assert "virtual_sorting" in analysis
    sorting = analysis["virtual_sorting"]
    assert "streams" in sorting
    print("\nVirtual Sorting Streams Breakdown:")
    for stream_name, stream_data in sorting["streams"].items():
        print(f"  Stream [{stream_name}]: {stream_data['count']} items ({stream_data['percentage']}%) -> {stream_data['diverter_bin']}")

    print("\nSimulated Diverter Events:")
    for event in sorting["diverter_events"]:
        print(f"  {event}")

    # Check MySQL persistence
    db = SessionLocal()
    try:
        session_db = db.query(WasteAnalysis).filter(WasteAnalysis.session_id == session_id).first()
        assert session_db is not None
        assert session_db.total_objects == len(detected_objs)
        print(f"\nPASS: Session record #{session_db.id} verified in MySQL database.")

        objs_db = db.query(DetectedObject).filter(DetectedObject.session_id == session_id).all()
        assert len(objs_db) == len(detected_objs)
        print(f"PASS: {len(objs_db)} detected objects persisted in detected_objects table.")
    finally:
        db.close()


def test_session_detail_endpoint():
    print("\n--- 2. TESTING GET /api/sessions/{session_id} ---")
    # Get latest session from results
    res_list = client.get("/api/results")
    assert res_list.status_code == 200
    latest_session_id = res_list.json()[0]["session_id"]

    res_detail = client.get(f"/api/sessions/{latest_session_id}")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert "session" in detail_data
    assert "detected_objects" in detail_data
    print(f"PASS: Session {latest_session_id} retrieved with {len(detail_data['detected_objects'])} objects.")


def test_statistics_endpoint():
    print("\n--- 3. TESTING GET /api/statistics ---")
    res_stats = client.get("/api/statistics")
    assert res_stats.status_code == 200
    stats = res_stats.json()
    print("Aggregate Statistics:", stats)
    assert "total_objects_detected" in stats
    assert "plastic_objects" in stats
    assert "review_queue_objects" in stats
    print("PASS: Stream and object aggregate statistics verified.")


def test_review_queue_and_reclassify():
    print("\n--- 4. TESTING HUMAN REVIEW QUEUE & RECLASSIFICATION ---")
    import uuid
    unique_sess_id = f"sess_test_rev_{uuid.uuid4().hex[:8]}"

    # Ensure there is at least one item in the review queue to test
    db = SessionLocal()
    test_obj_id = None
    try:
        # Create a test session with a review object
        test_session = WasteAnalysis(
            session_id=unique_sess_id,
            material="unknown",
            confidence=0.35,
            contamination_level="medium",
            contamination_percentage=30,
            quality_score=60,
            recycling_yield=50,
            recommendation="Manual verification required",
            total_objects=1,
            plastic_count=0,
            glass_count=0,
            metal_count=0,
            paper_count=0,
            organic_count=0,
            review_count=1,
            mode="REAL_YOLO",
            image_name="test_ambiguous.jpg",
        )
        db.add(test_session)
        db.flush()

        test_obj = DetectedObject(
            analysis_id=test_session.id,
            session_id=unique_sess_id,
            object_id="obj_ambiguous_1",
            material="unknown",
            confidence=0.35,
            box_x=50.0,
            box_y=50.0,
            box_width=100.0,
            box_height=100.0,
            stream="review",
            status="pending_review",
        )
        db.add(test_obj)
        db.commit()
        db.refresh(test_obj)
        test_obj_id = test_obj.id
    finally:
        db.close()

    res_queue = client.get("/api/review-queue")
    assert res_queue.status_code == 200
    items = res_queue.json()
    print(f"Current Review Queue size: {len(items)} items pending review.")
    assert len(items) > 0, "Expected at least 1 item in review queue"

    # Reclassify the test item
    reclass_res = client.post(
        f"/api/review-queue/{test_obj_id}/reclassify",
        json={"new_material": "plastic", "notes": "Human reviewer verified high-density polyethylene"}
    )
    assert reclass_res.status_code == 200
    reclass_data = reclass_res.json()
    assert reclass_data["success"] is True
    assert reclass_data["object"]["stream"] == "plastic"
    assert reclass_data["object"]["status"] == "reclassified"
    print(f"PASS: Reclassified item #{test_obj_id} to 'plastic' ({reclass_data['object']['stream']} stream).")

    # Verify item is no longer in pending review queue
    res_queue_after = client.get("/api/review-queue")
    remaining_ids = [it["id"] for it in res_queue_after.json()]
    assert test_obj_id not in remaining_ids, "Reclassified item should not be in pending review queue"
    print(f"PASS: Item #{test_obj_id} successfully cleared from active review queue.")


if __name__ == "__main__":
    print("=== EXECUTING PHASE 1 VIRTUAL SORTING PIPELINE VERIFICATION ===")
    test_full_virtual_sorting_pipeline()
    test_session_detail_endpoint()
    test_statistics_endpoint()
    test_review_queue_and_reclassify()
    print("\n=== ALL VIRTUAL SORTING PIPELINE TESTS PASSED! ===")
