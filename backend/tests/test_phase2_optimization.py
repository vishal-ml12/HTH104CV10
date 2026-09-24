"""
Phase 2 Verification Test Suite:
Validates stream-wise contamination analysis, quality scoring, recycling yield estimation,
yield-loss breakdown, mass balance, explainable recommendations, batch processing, and analytics.
"""

import os
import sys
import io
import uuid
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.session import SessionLocal
from backend.models import WasteAnalysis, DetectedObject, StreamAnalysis

client = TestClient(app)


def create_dummy_image_bytes(color=(40, 180, 80), size=(300, 300)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_phase2_stream_wise_pipeline():
    print("\n--- 1. TESTING POST /api/analyze WITH PHASE 2 OPTIMIZATION ---")
    bottle_path = r"C:\Users\sysadmin\Pictures\empty-green-used-water-bottle-recycling-145080483.webp"
    assert os.path.exists(bottle_path), f"Bottle image not found at {bottle_path}"

    with open(bottle_path, "rb") as f:
        file_bytes = f.read()

    res = client.post(
        "/api/analyze",
        files={"file": ("green_bottle.webp", file_bytes, "image/webp")},
        data={"input_mass_kg": 250.0}
    )
    assert res.status_code == 200, f"Error: {res.text}"

    data = res.json()
    assert data["success"] is True
    session_id = data["session_id"]
    print(f"Generated Phase 2 Session ID: {session_id}")

    analysis = data["analysis"]
    assert "streams_analysis" in analysis
    assert "optimization" in analysis
    assert "recommendation_reason" in analysis
    assert "processing_route" in analysis

    opt = analysis["optimization"]
    print(f"Primary Material: {opt['primary_material']} (Confidence: {opt['confidence']})")
    print(f"Input Mass: {opt['input_mass_kg']} kg | Recoverable: {opt['recoverable_mass_kg']} kg | Loss: {opt['waste_loss_kg']} kg")
    print(f"Quality Score: {opt['quality_score']}/100 | Yield: {opt['recycling_yield']}%")
    print(f"Processing Route: {opt['processing_route']}")
    print(f"Recommendation: {opt['recommendation']}")
    print(f"Reason: {opt['recommendation_reason']}")

    loss = opt["yield_loss_breakdown"]
    print(f"Yield Loss Breakdown: Baseline={loss['baseline_potential']}%, Handling Loss={loss['mechanical_handling_loss']}%, Contam Loss={loss['contamination_rejection_loss']}%, Net Yield={loss['net_estimated_yield']}%")

    # Verify stream-wise analysis
    streams_analysis = analysis["streams_analysis"]
    print("\nStream-Wise Contamination & Recovery Analysis:")
    for s_name, s_data in streams_analysis.items():
        print(f"  Stream [{s_name}]: {s_data['item_count']} items ({s_data['stream_share_pct']}%) | Contam: {s_data['contamination_percentage']}% ({s_data['contamination_category']}) | Yield: {s_data['estimated_yield']}% | Route: {s_data['processing_route']}")

    # Verify MySQL Persistence
    db = SessionLocal()
    try:
        session_db = db.query(WasteAnalysis).filter(WasteAnalysis.session_id == session_id).first()
        assert session_db is not None
        assert session_db.input_mass_kg == 250.0
        assert session_db.recoverable_mass_kg == opt["recoverable_mass_kg"]
        assert session_db.processing_route == opt["processing_route"]
        assert session_db.recommendation_reason is not None
        print(f"\nPASS: waste_analysis record #{session_db.id} verified with Phase 2 fields in MySQL.")

        streams_db = db.query(StreamAnalysis).filter(StreamAnalysis.session_id == session_id).all()
        assert len(streams_db) == 6
        print(f"PASS: 6 stream_analyses records persisted in MySQL.")

        objs_db = db.query(DetectedObject).filter(DetectedObject.session_id == session_id).all()
        assert len(objs_db) > 0
        for obj in objs_db:
            assert obj.contamination_score >= 0.0
            assert obj.contamination_category is not None
        print(f"PASS: {len(objs_db)} detected_objects verified with contamination fields.")
    finally:
        db.close()


def test_session_detail_endpoint():
    print("\n--- 2. TESTING GET /api/sessions/{session_id} WITH STREAM ANALYSES ---")
    res_list = client.get("/api/results")
    assert res_list.status_code == 200
    latest_session_id = res_list.json()[0]["session_id"]

    res_detail = client.get(f"/api/sessions/{latest_session_id}")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert "session" in detail_data
    assert "detected_objects" in detail_data
    assert "stream_analyses" in detail_data
    print(f"PASS: Session {latest_session_id} retrieved with {len(detail_data['stream_analyses'])} stream analysis records.")


def test_batch_analyze_endpoint():
    print("\n--- 3. TESTING POST /api/batch-analyze ---")
    img1 = ("img1.jpg", create_dummy_image_bytes(color=(30, 100, 200)), "image/jpeg")
    img2 = ("img2.jpg", create_dummy_image_bytes(color=(200, 150, 50)), "image/jpeg")

    res = client.post(
        "/api/batch-analyze",
        files=[("files", img1), ("files", img2)],
        data={"input_mass_kg": 500.0}
    )
    assert res.status_code == 200
    batch_data = res.json()
    assert batch_data["success"] is True
    assert batch_data["batch_size"] == 2
    summary = batch_data["batch_summary"]
    print("Batch Processing Summary:", summary)
    assert summary["total_input_mass_kg"] == 500.0
    assert summary["total_recoverable_kg"] > 0
    print("PASS: Batch analysis endpoint verified with multi-file yield calculation.")


def test_analytics_endpoints():
    print("\n--- 4. TESTING GET /api/analytics/trends & /api/analytics/streams ---")
    res_trends = client.get("/api/analytics/trends")
    assert res_trends.status_code == 200
    trends = res_trends.json()
    assert "contamination_trend" in trends
    assert "quality_trend" in trends
    assert "yield_trend" in trends
    print(f"PASS: Analytics trends retrieved ({len(trends['timestamps'])} sessions).")

    res_streams = client.get("/api/analytics/streams")
    assert res_streams.status_code == 200
    stream_analytics = res_streams.json()
    assert "streams" in stream_analytics
    for s_name, s_stat in stream_analytics["streams"].items():
        print(f"  Stream [{s_name}]: Avg Contam={s_stat['avg_contamination']}%, Avg Quality={s_stat['avg_quality']}, Avg Yield={s_stat['avg_yield']}%")
    print("PASS: Stream comparison analytics verified.")


if __name__ == "__main__":
    print("=== EXECUTING PHASE 2 OPTIMIZATION PIPELINE VERIFICATION ===")
    test_phase2_stream_wise_pipeline()
    test_session_detail_endpoint()
    test_batch_analyze_endpoint()
    test_analytics_endpoints()
    print("\n=== ALL PHASE 2 VERIFICATION TESTS PASSED! ===")
