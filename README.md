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

## 3. Installer DECA

DECA doit être installé séparément sur l'ordinateur de test.

```powershell
cd D:\
git clone https://github.com/YadiraF/DECA.git deca_install\\DECA
cd deca_install\\DECA
python -m venv venv_deca_test
.\\venv_deca_test\\Scripts\\activate
pip install -r requirements.txt
```

Les modèles préentraînés DECA et les fichiers FLAME doivent être téléchargés séparément depuis les ressources indiquées dans la documentation officielle DECA. Ils doivent ensuite être placés dans :

```text
D:\\deca_install\\DECA\\data\\
```

Le code et les modèles DECA sont séparés afin de ne pas inclure les fichiers lourds ou soumis à des conditions de distribution dans le dépôt de l'application.

## 4. Vérifier l'installation DECA

Vérifier la présence de :

```text
D:\\deca_install\\DECA\\demos\\demo_reconstruct.py
D:\\deca_install\\DECA\\data\\
D:\\deca_install\\DECA\\venv_deca_test\\Scripts\\python.exe
```

Tester DECA directement :

```powershell
cd D:\\deca_install\\DECA
.\\venv_deca_test\\Scripts\\python.exe demos\\demo_reconstruct.py -i TestSamples\\examples --saveObj True
```

Si le test se termine sans erreur et produit un fichier `.obj`, DECA est correctement installé.

## 5. Configurer DECA dans l'application

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

## 6. Démarrer le backend

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

## 7. Démarrer le frontend

Dans un deuxième terminal, depuis la racine du projet :

```powershell
python -m http.server 5510
```

Application :

```text
http://127.0.0.1:5510
```

## 8. Tester

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
