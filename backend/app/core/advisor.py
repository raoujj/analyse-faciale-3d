from typing import List, Dict

class AestheticAdvisor:
    def __init__(self, measurements: Dict):
        self.measurements = measurements
        self.recommendations = []
    
    def analyze(self) -> List[Dict]:
        self._check_nose()
        self._check_chin()
        self._check_symmetry()
        return self.recommendations
    
    def _add(self, zone, issue, suggestion, priority):
        self.recommendations.append({
            'zone': zone,
            'issue': issue,
            'suggestion': suggestion,
            'priority': priority
        })
    
    def _check_nose(self):
        ratios = self.measurements.get('ratios', {})
        eye_to_nose = ratios.get('eye_to_nose', 0)
        if eye_to_nose < 1.5:
            self._add('Nez', f'Largeur excessive: {eye_to_nose}', 'Rhinoplastie', 'high')
    
    def _check_chin(self):
        distances = self.measurements.get('distances', {})
        chin = distances.get('chin_projection', 0)
        if chin < 6:
            self._add('Menton', f'Projection faible: {chin}mm', 'Genioplastie', 'high')
    
    def _check_symmetry(self):
        symmetry = self.measurements.get('symmetry', {})
        overall = symmetry.get('overall', 100)
        if overall < 85:
            self._add('Symetrie', f'Asymetrie: {overall}%', 'Evaluation', 'medium')