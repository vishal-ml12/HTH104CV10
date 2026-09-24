import os
import sys
import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)

test_files = [
    ("Plastic Bottle", r"C:\Users\sysadmin\Pictures\empty-green-used-water-bottle-recycling-145080483.webp"),
    ("Metal Can/Sample", r"C:\Users\sysadmin\Pictures\download.webp"),
    ("Paper/Cardboard", r"C:\Users\sysadmin\Downloads\slide 2 diagram.png"),
    ("Mixed Waste", r"C:\Users\sysadmin\Pictures\OIP (1).webp"),
    ("Uncertain Object", r"C:\Users\sysadmin\Pictures\OIP.webp"),
]

print("=== REAL COMPUTER VISION MODEL EVALUATION ===")
print("Testing live endpoint POST /api/analyze with real image files...\n")

results = []
for label, path in test_files:
    if not os.path.exists(path):
        print(f"Skipping {label}: file not found at {path}")
        continue

    with open(path, "rb") as f:
        file_bytes = f.read()

    filename = os.path.basename(path)
    res = client.post("/api/analyze", files={"file": (filename, file_bytes, "image/png")})
    assert res.status_code == 200, f"Error for {label}: {res.text}"

    data = res.json()["analysis"]
    mat_info = data["materials"][0]
    results.append((label, mat_info["name"], mat_info["confidence"], data["contamination"]["percentage"], data["contamination"]["level"], data["quality_score"], data["recycling_yield"], data["recommendation"]))

    print(f"Sample: {label}")
    print(f"  File: {filename}")
    print(f"  Predicted Material: {mat_info['name'].upper()}")
    print(f"  Model Confidence:   {mat_info['confidence']:.2%}")
    print(f"  Contamination:      {data['contamination']['percentage']}% ({data['contamination']['level']})")
    print(f"  Quality Score:      {data['quality_score']} / 100")
    print(f"  Recycling Yield:    {data['recycling_yield']}%")
    print(f"  Recommendation:     {data['recommendation']}\n")

# Verify Plastic Bottle was correctly classified as plastic
plastic_results = [r for r in results if r[0] == "Plastic Bottle"]
assert len(plastic_results) > 0
assert plastic_results[0][1] == "plastic", f"Expected plastic, got {plastic_results[0][1]}"
print("VERIFICATION CHECK: Plastic Bottle test passed with real model prediction!")

# Check results and statistics endpoints
r_res = client.get("/api/results")
assert r_res.status_code == 200
r_stats = client.get("/api/statistics")
assert r_stats.status_code == 200

print(f"\nLive Database Records: {len(r_res.json())} entries stored.")
print(f"Live Database Aggregate Statistics: {r_stats.json()}")
print("\n=== ALL VISION MODEL TESTS COMPLETED SUCCESSFULLY ===")
