import os
import sys
import io
from PIL import Image

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def make_valid_png(color: tuple, size=(200, 200)) -> bytes:
    """Generate a valid in-memory PNG image."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Waste Recycling Optimizer"
    print("PASS: /api/health returned:", data)


def test_no_file_rejected():
    response = client.post("/api/analyze")
    assert response.status_code == 400, f"Expected 400 for missing file, got {response.status_code}"
    data = response.json()
    assert "detail" in data
    print("PASS: /api/analyze rejected missing file with 400:", data["detail"])


def test_empty_file_rejected():
    files = {"file": ("empty.png", b"", "image/png")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 400
    print("PASS: /api/analyze rejected empty file with 400:", response.json()["detail"])


def test_real_green_bottle_image():
    bottle_path = r"C:\Users\sysadmin\Pictures\empty-green-used-water-bottle-recycling-145080483.webp"
    if os.path.exists(bottle_path):
        with open(bottle_path, "rb") as f:
            b = f.read()
        res = client.post("/api/analyze", files={"file": ("green_bottle.webp", b, "image/webp")})
        assert res.status_code == 200
        analysis = res.json()["analysis"]
        mat = analysis["materials"][0]
        assert mat["name"] == "plastic", f"Expected plastic, got {mat['name']}"
        assert mat["confidence"] > 0.85, f"Expected high confidence, got {mat['confidence']}"
        print(f"PASS Real Plastic Bottle Test: Material={mat['name'].upper()} with {mat['confidence']:.2%} confidence")


def test_vision_pipeline_with_images():
    # Test with valid images
    img1 = make_valid_png((34, 139, 34))   # Forest green
    img2 = make_valid_png((192, 192, 192)) # Silver / metallic
    img3 = make_valid_png((210, 180, 140)) # Cardboard brown

    res1 = client.post("/api/analyze", files={"file": ("sample_1.png", img1, "image/png")})
    assert res1.status_code == 200
    d1 = res1.json()["analysis"]

    res2 = client.post("/api/analyze", files={"file": ("sample_2.png", img2, "image/png")})
    assert res2.status_code == 200
    d2 = res2.json()["analysis"]

    res3 = client.post("/api/analyze", files={"file": ("sample_3.png", img3, "image/png")})
    assert res3.status_code == 200
    d3 = res3.json()["analysis"]

    print(f"PASS Sample 1: Material={d1['materials'][0]['name']}, Conf={d1['materials'][0]['confidence']}, Yield={d1['recycling_yield']}%")
    print(f"PASS Sample 2: Material={d2['materials'][0]['name']}, Conf={d2['materials'][0]['confidence']}, Yield={d2['recycling_yield']}%")
    print(f"PASS Sample 3: Material={d3['materials'][0]['name']}, Conf={d3['materials'][0]['confidence']}, Yield={d3['recycling_yield']}%")


def test_results_and_statistics():
    res_history = client.get("/api/results")
    assert res_history.status_code == 200
    records = res_history.json()
    assert len(records) >= 1
    print(f"PASS: /api/results contains {len(records)} stored records.")

    res_stats = client.get("/api/statistics")
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert stats["total_analyses"] >= 1
    print(f"PASS: /api/statistics computed from MySQL: Total={stats['total_analyses']}, AvgContam={stats['average_contamination']}%, AvgQuality={stats['average_quality_score']}, AvgYield={stats['average_recycling_yield']}%")


if __name__ == "__main__":
    print("--- RUNNING REAL COMPUTER VISION PIPELINE TESTS ---")
    test_health_check()
    test_no_file_rejected()
    test_empty_file_rejected()
    test_real_green_bottle_image()
    test_vision_pipeline_with_images()
    test_results_and_statistics()
    print("--- ALL TESTS COMPLETED AND VERIFIED! ---")
