import requests

url = "http://127.0.0.1:8000/analyze"
photo_path = r"E:\test-pic-face.jpeg"

with open(photo_path, "rb") as f:
    r = requests.post(url, files={"file": f})
    result = r.json()["data"]
    
    print("=== MESURES ===")
    for k, v in result["measurements"]["distances"].items():
        print(f"  {k}: {v} mm")
    
    print()
    print("=== RATIOS ===")
    for k, v in result["measurements"]["ratios"].items():
        print(f"  {k}: {v}")
    
    print()
    print("=== SCORES ===")
    for k, v in result["measurements"]["scores"].items():
        print(f"  {k}: {v}%")
    
    print()
    print("=== RECOMMANDATIONS ===")
    for rec in result["recommendations"]:
        priority = rec["priority"].upper()
        zone = rec["zone"]
        suggestion = rec["suggestion"]
        print(f"  [{priority}] {zone}: {suggestion}")