import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000")

png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
img1 = png_header + b"\x00\x00\x00\x10\x00\x00\x00\x10\x08\x02\x00\x00\x00WASTE_PLASTIC_WATER_BOTTLE_2026"
img2 = png_header + b"\x00\x00\x00\x20\x00\x00\x00\x20\x08\x02\x00\x00\x00WASTE_CRUSHED_CAN_METAL_2026"
img3 = png_header + b"\x00\x00\x00\x30\x00\x00\x00\x30\x08\x02\x00\x00\x00WASTE_OLD_CARDBOARD_BOX_2026"

print("--- 1. TESTING LIVE HEALTH ENDPOINT ---")
r_health = client.get("/api/health")
print("Health status:", r_health.status_code, r_health.json())

print("\n--- 2. TESTING LIVE ANALYZE WITH 3 DIFFERENT IMAGES ---")
samples = [
    ("plastic_bottle.png", img1),
    ("soda_can.png", img2),
    ("cardboard.png", img3),
]

for idx, (name, img_data) in enumerate(samples, 1):
    res = client.post("/api/analyze", files={"file": (name, img_data, "image/png")})
    assert res.status_code == 200, f"Error: {res.text}"
    analysis = res.json()["analysis"]
    mat = analysis["materials"][0]
    contam = analysis["contamination"]
    print(f"Upload {idx} ({name}): HTTP {res.status_code}")
    print(f"   Material: {mat['name']}")
    print(f"   Confidence: {mat['confidence']}")
    print(f"   Contamination: {contam['percentage']}% ({contam['level']})")
    print(f"   Quality Score: {analysis['quality_score']}/100")
    print(f"   Recycling Yield: {analysis['recycling_yield']}%")
    print(f"   Recommendation: {analysis['recommendation']}")

print("\n--- 3. TESTING DETERMINISTIC RE-UPLOAD (SAME IMAGE) ---")
res_repeat = client.post("/api/analyze", files={"file": ("plastic_bottle.png", img1, "image/png")})
assert res_repeat.status_code == 200
analysis_repeat = res_repeat.json()["analysis"]
print("Re-uploading plastic_bottle.png produced:")
print(f"   Material: {analysis_repeat['materials'][0]['name']}")
print(f"   Contamination: {analysis_repeat['contamination']['percentage']}%")
print(f"   Yield: {analysis_repeat['recycling_yield']}%")
assert analysis_repeat == client.post("/api/analyze", files={"file": ("plastic_bottle.png", img1, "image/png")}).json()["analysis"]
print("PASS: Exact same values produced on repeated upload!")

print("\n--- 4. TESTING GET /api/results ---")
r_results = client.get("/api/results")
assert r_results.status_code == 200
latest_records = r_results.json()[:4]
for rec in latest_records:
    print(f"DB Record #{rec['id']}: Material={rec['material']} | Contam={rec['contamination_percentage']}% | Quality={rec['quality_score']} | Yield={rec['recycling_yield']}% | Rec='{rec['recommendation']}'")

print("\n--- 5. TESTING GET /api/statistics ---")
r_stats = client.get("/api/statistics")
assert r_stats.status_code == 200
stats = r_stats.json()
print("Live DB Aggregate Statistics:")
print(f"   Total Analyses: {stats['total_analyses']}")
print(f"   Average Contamination: {stats['average_contamination']}%")
print(f"   Average Quality Score: {stats['average_quality_score']}/100")
print(f"   Average Recycling Yield: {stats['average_recycling_yield']}%")

print("\n--- 6. TESTING CACHE-CONTROL HEADERS ---")
print("Results Cache-Control header:", r_results.headers.get("cache-control"))
print("Statistics Cache-Control header:", r_stats.headers.get("cache-control"))
assert "no-cache" in r_results.headers.get("cache-control", "")
assert "no-cache" in r_stats.headers.get("cache-control", "")
print("PASS: Cache prevention headers verified.")

print("\n--- 7. TESTING ERROR HANDLING (MISSING / INVALID FILE) ---")
err1 = client.post("/api/analyze")
print("No file upload status:", err1.status_code, err1.json())
assert err1.status_code == 400

err2 = client.post("/api/analyze", files={"file": ("test.txt", b"plain text", "text/plain")})
print("Invalid file type status:", err2.status_code, err2.json())
assert err2.status_code == 400

print("\n=== ALL LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY! ===")
