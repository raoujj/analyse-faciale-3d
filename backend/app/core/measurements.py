import numpy as np
from typing import Dict, List

class MeasurementCalculator:
    def __init__(self, landmarks: List[Dict], image_width: int, image_height: int):
        self.landmarks = landmarks
        self.w = image_width
        self.h = image_height
        
        # Échelle : distance inter-oculaire moyenne adulte = 63mm
        left_eye = self._point(33)
        right_eye = self._point(263)
        self.inter_ocular_px = np.linalg.norm(left_eye - right_eye)
        self.scale = 63.0 / self.inter_ocular_px if self.inter_ocular_px > 0 else 1.0
    
    def _point(self, idx: int) -> np.ndarray:
        lm = self.landmarks[idx]
        return np.array([lm['x'] * self.w, lm['y'] * self.h, lm['z'] * self.w])
    
    def _distance_px(self, i: int, j: int) -> float:
        return np.linalg.norm(self._point(i) - self._point(j))
    
    def _distance_mm(self, i: int, j: int) -> float:
        return self._distance_px(i, j) * self.scale
    
    def calculate_all(self) -> Dict:
        # POINTS CLÉS MEDIAPIPE
        LEFT_EYE = 33
        RIGHT_EYE = 263
        NOSE_LEFT = 129
        NOSE_RIGHT = 358
        NOSE_TIP = 1
        NOSE_BRIDGE = 6
        MOUTH_LEFT = 61
        MOUTH_RIGHT = 291
        FOREHEAD = 10
        CHIN = 152
        LEFT_CHEEK = 234
        RIGHT_CHEEK = 454
        
        # DISTANCES EN MM
        inter_ocular = self._distance_mm(LEFT_EYE, RIGHT_EYE)
        nose_width = self._distance_mm(NOSE_LEFT, NOSE_RIGHT)
        nose_height = self._distance_mm(NOSE_BRIDGE, NOSE_TIP)
        mouth_width = self._distance_mm(MOUTH_LEFT, MOUTH_RIGHT)
        face_height = self._distance_mm(FOREHEAD, CHIN)
        face_width = self._distance_mm(LEFT_CHEEK, RIGHT_CHEEK)
        
        # RATIOS
        eye_to_nose = inter_ocular / nose_width if nose_width > 0 else 0
        face_ratio = face_height / face_width if face_width > 0 else 0
        
        # SCORES
        golden_ratio_ideal = 1.618
        golden_score = max(0, 100 - abs(eye_to_nose - golden_ratio_ideal) / golden_ratio_ideal * 100)
        
        return {
            "distances": {
                "inter_ocular": round(inter_ocular, 1),
                "nose_width": round(nose_width, 1),
                "nose_height": round(nose_height, 1),
                "mouth_width": round(mouth_width, 1),
                "face_height": round(face_height, 1),
                "face_width": round(face_width, 1),
            },
            "ratios": {
                "eye_to_nose": round(eye_to_nose, 3),
                "face_height_to_width": round(face_ratio, 3),
                "golden_ratio_conformity": round(golden_score, 1),
            },
            "scores": {
                "global": round(golden_score, 1),
            }
        }