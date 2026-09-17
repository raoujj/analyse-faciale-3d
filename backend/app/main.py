from pathlib import Path
import shutil
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.core.deca_service import DECAService


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = BASE_DIR / "deca-results"
UPLOADS_DIR = OUTPUT_ROOT / "_uploads"
FRONTEND_DIR = BASE_DIR / "frontend"

OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="DECA Facial Simulation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5510",
        "http://localhost:5510",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

deca_service = DECAService(output_root=OUTPUT_ROOT)

app.mount("/deca-results", StaticFiles(directory=str(OUTPUT_ROOT)), name="deca-results")

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


class SimulateRequest(BaseModel):
    session_id: str
    tipProjection: float = Field(default=0.0, ge=-2.0, le=2.0)
    tipRotation: float = Field(default=0.0, ge=-2.0, le=2.0)
    bridge: float = Field(default=0.0, ge=-2.0, le=2.0)
    alarWidth: float = Field(default=0.0, ge=-2.0, le=2.0)
    chin: float = Field(default=0.0, ge=-2.0, le=2.0)
    jaw: float = Field(default=0.0, ge=-2.0, le=2.0)


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "deca-facial-simulation",
        "output_root": str(OUTPUT_ROOT),
    }


@app.post("/reconstruct")
async def reconstruct(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant.")

    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image.")

    ext = Path(file.filename).suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Format image non supporté.")

    session_id = str(uuid.uuid4())
    upload_path = UPLOADS_DIR / f"{session_id}{ext}"

    try:
        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = deca_service.reconstruct_face(
            session_id=session_id,
            image_path=upload_path,
        )

        return {
            "ok": True,
            "session_id": session_id,
            "obj_url": result["obj_url"],
            "mtl_url": result["mtl_url"],
            "texture_url": result.get("texture_url"),
            "preview_url": result.get("preview_url"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur reconstruction: {str(e)}")
    finally:
        await file.close()


@app.post("/simulate")
def simulate(req: SimulateRequest):
    try:
        result = deca_service.simulate_face(
            session_id=req.session_id,
            tip_projection=req.tipProjection,
            tip_rotation=req.tipRotation,
            bridge=req.bridge,
            alar_width=req.alarWidth,
            chin=req.chin,
            jaw=req.jaw,
        )
        return {
            "ok": True,
            "session_id": req.session_id,
            "obj_url": result["obj_url"],
            "mtl_url": result["mtl_url"],
            "texture_url": result.get("texture_url"),
            "preview_url": result.get("preview_url"),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur simulation: {str(e)}")