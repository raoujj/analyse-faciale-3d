import requests
import base64

url = "http://127.0.0.1:8000/analyze"
photo_path = r"E:\test-pic-face.jpeg"

with open(photo_path, "rb") as f:
    response = requests.post(url, files={"file": f})
    result = response.json()

# Sauvegarder l'image annotée
if result["success"]:
    img_data = result["data"]["annotated_image"].split(",")[1]
    img_bytes = base64.b64decode(img_data)
    
    with open("resultat_annotated.jpg", "wb") as f:
        f.write(img_bytes)
    
    print("✅ Image sauvegardée : resultat_annotated.jpg")
    print(f"📊 Landmarks : {result['data']['landmarks_count']}")
    print(f"📐 Taille : {result['data']['image_size']}")