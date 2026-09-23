# Analyse faciale 3D

Application de reconstruction faciale 3D à partir d’une photo. Le projet utilise DECA pour la reconstruction, PyTorch3D pour les composants 3D, un backend FastAPI et un viewer web statique.

## Fonctionnalités

- Importer une photo de visage.
- Reconstruire un visage 3D avec DECA.
- Afficher le modèle 3D dans le viewer web.
- Modifier certains paramètres de simulation faciale.
- Utiliser une API FastAPI entre le front et le moteur DECA.

## Structure du projet

```text
analyse-faciale-3d/
├── backend/
├── external/
│   ├── DECA/
│   └── pytorch3d/
├── mobile_app/
├── .gitignore
└── README.md
```

## Prérequis Windows

Installer :

- Git.
- Python 3.11 64 bits.
- Visual Studio Build Tools avec la charge « Desktop development with C++ ».
- Le Windows SDK.
- Un terminal « x64 Native Tools Command Prompt for VS 2022 ».

Vérifier Python :

```cmd
py -3.11-64 -c "import platform,struct; print(platform.architecture()); print(struct.calcsize('P')*8)"
```

Le résultat doit indiquer `64bit` et `64`.

## Télécharger le modèle DECA

Le fichier `deca_model.tar` est nécessaire pour la reconstruction DECA. Il n’est pas inclus dans GitHub à cause de sa taille.

Téléchargement :

[ Télécharger deca_model.tar ](https://drive.usercontent.google.com/download?id=1rp8kdyLPvErw2dTmqtjISRVvQLj6Yzje&export=download&authuser=0)

Ne pas décompresser le fichier. Le placer ici :

```text
external/DECA/data/deca_model.tar
```

Vérifier :

```powershell
Test-Path .\external\DECA\data\deca_model.tar
```

Le résultat attendu est `True`.

## Cloner le projet

```cmd
git clone https://github.com/raoujj/analyse-faciale-3d.git
cd analyse-faciale-3d
```

## Créer l’environnement Python

Depuis un terminal x64 :

```cmd
cd external\DECA
py -3.11-64 -m venv venv_deca_test
venv_deca_test\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install "fastapi[standard]"
```

Vérifier que l’environnement utilise le bon Python :

```cmd
python -c "import sys,platform,struct; print(sys.executable); print(platform.architecture()); print(struct.calcsize('P')*8)"
```

## Installer PyTorch3D

Toujours avec l’environnement activé :

```cmd
cd ..\pytorch3d
set DISTUTILS_USE_SDK=1
set MAX_JOBS=2
python -m pip install --no-build-isolation .
```

Tester :

```cmd
python -c "import torch,pytorch3d; print('Torch:',torch.__version__); print('PyTorch3D:',pytorch3d.__version__); print('PyTorch3D OK')"
```

## Lancer le backend

Ouvrir un terminal et exécuter :

```cmd
cd /d E:\analyse-faciale-3d
external\DECA\venv_deca_test\Scripts\activate.bat
python -m uvicorn app.main:app --app-dir backend --reload
```

Backend : http://127.0.0.1:8000
Documentation API : http://127.0.0.1:8000/docs

## Lancer le front

Ouvrir un deuxième terminal :

```powershell
cd E:\analyse-faciale-3d\mobile_app
python -m http.server 5500
```

Ouvrir ensuite : http://localhost:5500

## Vérification rapide

1. Ouvrir le front sur `http://localhost:5500`.
2. Sélectionner une photo.
3. Cliquer sur « Reconstruire ».
4. Attendre la réponse du backend.
5. Vérifier l’affichage du modèle 3D.

## Dépannage

### No module named uvicorn

```cmd
pip install "fastapi[standard]"
```

### No module named app

Depuis la racine du projet, utiliser :

```cmd
python -m uvicorn app.main:app --app-dir backend --reload
```

### PyTorch3D ne se compile pas

Vérifier que Python est 64 bits et utiliser « x64 Native Tools Command Prompt for VS 2022 ». Vérifier que `where cl` et `where link` montrent `Hostx64\x64`.

### deca_model.tar manquant

Télécharger le modèle et le placer dans `external/DECA/data/deca_model.tar` sans le décompresser.

### Le front ne se connecte pas au backend

Vérifier que les deux serveurs sont lancés et que le backend est disponible sur `http://127.0.0.1:8000`.

## Fichiers non inclus

Les éléments suivants ne doivent pas être commités :

- environnements virtuels Python ;
- dossiers `build` et `__pycache__` ;
- résultats temporaires ;
- fichiers de modèles volumineux non autorisés ;
- chemins absolus propres à un ordinateur.

Chaque utilisateur doit créer son propre environnement virtuel et fournir séparément les modèles requis.

## Licence et modèles

Respecter les licences de DECA, PyTorch3D, FLAME et des modèles téléchargés. Vérifier les conditions d’utilisation avant toute redistribution ou utilisation commerciale.
