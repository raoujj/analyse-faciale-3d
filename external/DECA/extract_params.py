import sys
sys.path.insert(0, '.')
import torch
import numpy as np
from decalib.deca import DECA
from decalib.utils.config import cfg as deca_cfg
from decalib.datasets import datasets

deca_cfg.rasterizer_type = 'pytorch3d'
deca_cfg.model.use_tex = False
deca = DECA(config=deca_cfg, device='cpu')

testdata = datasets.TestData(r'D:\analyse-faciale-3d\backend\resultat_annotated.jpg')
data = testdata[0]

with torch.no_grad():
    codedict = deca.encode(data['image'].unsqueeze(0))

shape = codedict['shape'].numpy()
exp   = codedict['exp'].numpy()
pose  = codedict['pose'].numpy()

print("=== SHAPE PARAMS (100) ===")
print(shape)
print("=== EXPRESSION PARAMS (50) ===")
print(exp)
print("=== POSE PARAMS (6) ===")
print(pose)

np.save('params_shape.npy', shape)
np.save('params_exp.npy', exp)
np.save('params_pose.npy', pose)
print("\nFichiers sauvegardes: params_shape.npy, params_exp.npy, params_pose.npy")
