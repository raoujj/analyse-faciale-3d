import cv2
import numpy as np
import base64

import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options

from app.core.measurements import MeasurementCalculator
from app.core.advisor import AestheticAdvisor

class FaceDetector:
    def __init__(self):
        model_path = "face_landmarker.task"
        
        self.options = vision.FaceLandmarkerOptions(
            base_options=base_options.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        
        self.detector = vision.FaceLandmarker.create_from_options(self.options)
    
    def detect(self, image_bytes):
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return None, "Image invalide"
        
        h, w, _ = image.shape
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        results = self.detector.detect(mp_image)
        
        if not results.face_landmarks:
            return None, "Aucun visage détecté"
        
        # Extraire les landmarks
        landmarks = []
        for lm in results.face_landmarks[0]:
            landmarks.append({
                "x": float(lm.x),
                "y": float(lm.y),
                "z": float(lm.z)
            })
        
        # Dessiner les landmarks
        annotated_image = image.copy()
        for lm in results.face_landmarks[0]:
            x = int(lm.x * w)
            y = int(lm.y * h)
            cv2.circle(annotated_image, (x, y), 1, (0, 255, 0), -1)
        
        _, buffer = cv2.imencode('.jpg', annotated_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # CALCULS DES MESURES
        calculator = MeasurementCalculator(landmarks, w, h)
        measurements = calculator.calculate_all()
        
        # RECOMMANDATIONS
        advisor = AestheticAdvisor(measurements)
        recommendations = advisor.analyze()
        
        return {
            "landmarks_count": len(landmarks),
            "landmarks": landmarks,
            "image_size": {"width": w, "height": h},
            "annotated_image": f"data:image/jpeg;base64,{img_base64}",
            "measurements": measurements,
            "recommendations": recommendations
        }, None