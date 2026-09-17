# Analyse faciale 3D

Application locale de reconstruction et de simulation faciale 3D avec DECA, FastAPI et Three.js.

## Prérequis

- Windows 10 ou Windows 11
- Git
- Python
- DECA installé séparément avec ses modèles

## 1. Cloner le projet

```powershell
git clone https://github.com/raoujj/analyse-faciale-3d.git
cd analyse-faciale-3d
```

## 2. Installer le backend

```powershell
cd backend
python -m venv venv
.\\venv\\Scripts\\activate
pip install -r requirements.txt
```

## 3. Configurer DECA

Ouvrir :

```text
backend/app/core/deca_service.py
```

Vérifier ce chemin :

```python
deca_root: Path | str = r"D:\\deca_install\\DECA"
```

Adapter le chemin si DECA est installé ailleurs.

DECA doit contenir :

```text
DECA/
├── data/
├── demos/
│   └── demo_reconstruct.py
└── venv_deca_test/
    └── Scripts/
        └── python.exe
```

Les modèles DECA doivent être téléchargés séparément.

## 4. Démarrer le backend

Dans un premier terminal :

```powershell
cd backend
.\\venv\\Scripts\\activate
python -m uvicorn app.main:app --reload
```

Backend :

```text
http://127.0.0.1:8000
```

## 5. Démarrer le frontend

Dans un deuxième terminal, depuis la racine du projet :

```powershell
python -m http.server 5510
```

Application :

```text
http://127.0.0.1:5510
```

## 6. Tester

1. Ouvrir `http://127.0.0.1:5510`.
2. Sélectionner une image JPG, JPEG, PNG ou WEBP.
3. Lancer la reconstruction.
4. Attendre la génération du modèle 3D.
5. Tester la simulation faciale.

## Résultats

Les fichiers générés sont enregistrés dans :

```text
backend/app/deca-results/
```

Le dossier contient notamment :

```text
OBJ
MTL
textures
preview
state.json
```

## Dépannage

Si l'erreur suivante apparaît :

```text
OBJ non généré par DECA
```

Vérifier :

- le chemin `deca_root` ;
- les modèles DECA dans le dossier `data` ;
- le fichier `demo_reconstruct.py` ;
- l'environnement `venv_deca_test` ;
- les messages affichés dans le terminal backend.
