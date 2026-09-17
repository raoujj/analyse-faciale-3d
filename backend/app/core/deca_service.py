from __future__ import annotations

from pathlib import Path
import json
import logging
import shutil
import subprocess
import uuid

import numpy as np


logger = logging.getLogger(__name__)


class DECAService:
    def __init__(
        self,
        output_root: Path,
        deca_root: Path | str = r"D:\deca_install\DECA",
        python_bin: Path | str | None = None,
        deca_timeout_seconds: int = 600,
    ):
        self.output_root = Path(output_root).resolve()
        self.sessions_dir = self.output_root / "_sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        self.deca_root = Path(deca_root).resolve()
        self.python_bin = Path(
            python_bin or (self.deca_root / "venv_deca_test" / "Scripts" / "python.exe")
        ).resolve()
        self.deca_timeout_seconds = int(deca_timeout_seconds)

        self.demo_script = (self.deca_root / "demos" / "demo_reconstruct.py").resolve()

        if not self.output_root.exists():
            self.output_root.mkdir(parents=True, exist_ok=True)

        if not self.deca_root.exists():
            raise RuntimeError(f"Dossier DECA introuvable: {self.deca_root}")
        if not self.demo_script.exists():
            raise RuntimeError(f"Script DECA introuvable: {self.demo_script}")
        if not self.python_bin.exists():
            raise RuntimeError(f"Python DECA introuvable: {self.python_bin}")

        logger.info(
            "DECAService initialisé | output_root=%s | deca_root=%s | python_bin=%s",
            self.output_root,
            self.deca_root,
            self.python_bin,
        )

    def reconstruct_face(self, session_id: str, image_path: Path) -> dict:
        image_path = Path(image_path).resolve()
        if not image_path.exists():
            raise FileNotFoundError(f"Image introuvable: {image_path}")

        session_dir = self.sessions_dir / session_id
        base_dir = session_dir / "base"
        base_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Reconstruction DECA | session_id=%s | image=%s", session_id, image_path)
        self._run_deca(image_path=image_path, output_dir=base_dir)

        obj_path = self._find_best_obj(base_dir)
        if obj_path is None:
            raise RuntimeError(f"OBJ non généré par DECA dans: {base_dir}")

        mtl_path = self._find_best_mtl(obj_path)
        texture_path = self._find_texture_near(obj_path)
        preview_path = self._find_preview(base_dir)

        state = {
            "session_id": session_id,
            "base_dir": str(base_dir),
            "input_image": str(image_path),
            "base_obj": str(obj_path),
            "base_mtl": str(mtl_path) if mtl_path and mtl_path.exists() else None,
            "base_texture": str(texture_path) if texture_path and texture_path.exists() else None,
        }
        self._save_state(session_id, state)

        result = self._public_result(obj_path, mtl_path, texture_path, preview_path)
        logger.info("Reconstruction terminée | session_id=%s | obj=%s", session_id, result["obj_url"])
        return result

    def simulate_face(
        self,
        session_id: str,
        tip_projection: float,
        tip_rotation: float,
        bridge: float,
        alar_width: float,
        chin: float,
        jaw: float,
    ) -> dict:
        state = self._load_state(session_id)
        if not state:
            raise FileNotFoundError("Session introuvable.")

        variant_id = str(uuid.uuid4())[:8]
        session_dir = self.sessions_dir / session_id
        variant_dir = session_dir / f"sim_{variant_id}"
        variant_dir.mkdir(parents=True, exist_ok=True)

        base_obj = Path(state["base_obj"]).resolve()
        if not base_obj.exists():
            raise FileNotFoundError(f"OBJ de base introuvable: {base_obj}")

        sim_obj = variant_dir / "simulated.obj"
        sim_mtl = variant_dir / "simulated.mtl"

        logger.info(
            "Simulation anatomique | session_id=%s | variant=%s | tip_projection=%.3f | tip_rotation=%.3f | bridge=%.3f | alar_width=%.3f | chin=%.3f | jaw=%.3f",
            session_id,
            variant_id,
            tip_projection,
            tip_rotation,
            bridge,
            alar_width,
            chin,
            jaw,
        )

        self._simulate_from_obj(
            src_obj=base_obj,
            dst_obj=sim_obj,
            tip_projection=tip_projection,
            tip_rotation=tip_rotation,
            bridge=bridge,
            alar_width=alar_width,
            chin=chin,
            jaw=jaw,
        )

        base_mtl = state.get("base_mtl")
        if base_mtl and Path(base_mtl).exists():
            shutil.copy2(base_mtl, sim_mtl)

        texture_path = None
        base_texture = state.get("base_texture")
        if base_texture and Path(base_texture).exists():
            src_tex = Path(base_texture)
            dst_tex = variant_dir / src_tex.name
            shutil.copy2(src_tex, dst_tex)
            texture_path = dst_tex

            if sim_mtl.exists():
                txt = sim_mtl.read_text(encoding="utf-8", errors="ignore")
                txt = txt.replace(src_tex.name, dst_tex.name)
                sim_mtl.write_text(txt, encoding="utf-8")

        result = self._public_result(sim_obj, sim_mtl, texture_path, None)
        logger.info("Simulation terminée | session_id=%s | obj=%s", session_id, result["obj_url"])
        return result

    def _run_deca(self, image_path: Path, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.python_bin),
            "demos/demo_reconstruct.py",
            "-i", str(image_path),
            "-s", str(output_dir),
            "--saveObj", "True",
            "--saveDepth", "True",
            "--saveKpt", "True",
            "--saveVis", "True",
            "--extractTex", "True",
            "--device", "cpu",
            "--rasterizer_type", "pytorch3d",
        ]

        logger.info("DECA cwd=%s", self.deca_root)
        logger.info("DECA python=%s", self.python_bin)
        logger.info("DECA cmd=%s", cmd)

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.deca_root),
                check=True,
                capture_output=True,
                text=True,
                timeout=self.deca_timeout_seconds,
            )
            if result.stdout:
                logger.info("DECA stdout:\n%s", result.stdout)
            if result.stderr:
                logger.warning("DECA stderr:\n%s", result.stderr)
        except subprocess.TimeoutExpired as e:
            logger.exception("Timeout DECA | image=%s", image_path)
            raise RuntimeError(
                f"DECA timeout après {self.deca_timeout_seconds}s pour l'image: {image_path}"
            ) from e
        except subprocess.CalledProcessError as e:
            logger.exception("Échec exécution DECA | image=%s", image_path)
            raise RuntimeError(f"DECA execution failed: {e.stderr or e.stdout or str(e)}") from e

    def _simulate_from_obj(
        self,
        src_obj: Path,
        dst_obj: Path,
        tip_projection: float,
        tip_rotation: float,
        bridge: float,
        alar_width: float,
        chin: float,
        jaw: float,
    ) -> None:
        vertices = []
        raw_lines = []

        with src_obj.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                raw_lines.append(line)
                if line.startswith("v "):
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])

        if not vertices:
            raise RuntimeError("OBJ invalide: aucun vertex.")

        v = np.array(vertices, dtype=np.float32)

        min_xyz = v.min(axis=0)
        max_xyz = v.max(axis=0)
        size = max_xyz - min_xyz
        center = (min_xyz + max_xyz) * 0.5

        width = max(float(size[0]), 1e-6)
        height = max(float(size[1]), 1e-6)
        depth = max(float(size[2]), 1e-6)

        def smooth_weight(value: float) -> float:
            if value <= 0.0:
                return 0.0
            t = min(1.0, max(0.0, value))
            return t * t * (3.0 - 2.0 * t)

        def ellipsoid_weight(
            x: float,
            y: float,
            z: float,
            cx: float,
            cy: float,
            cz: float,
            rx: float,
            ry: float,
            rz: float,
        ) -> float:
            dx = (x - cx) / max(rx, 1e-6)
            dy = (y - cy) / max(ry, 1e-6)
            dz = (z - cz) / max(rz, 1e-6)
            d2 = dx * dx + dy * dy + dz * dz
            if d2 >= 1.0:
                return 0.0
            return smooth_weight(1.0 - d2)

        def gate(
            y: float,
            z: float,
            y_min: float | None = None,
            y_max: float | None = None,
            z_min: float | None = None,
            z_max: float | None = None,
        ) -> float:
            w = 1.0
            if y_min is not None:
                w *= smooth_weight((y - y_min) / (height * 0.04))
            if y_max is not None:
                w *= smooth_weight((y_max - y) / (height * 0.04))
            if z_min is not None:
                w *= smooth_weight((z - z_min) / (depth * 0.05))
            if z_max is not None:
                w *= smooth_weight((z_max - z) / (depth * 0.05))
            return w

        y_neck_cut = min_xyz[1] + height * 0.24
        y_lower_face_cut = min_xyz[1] + height * 0.34
        y_nose_low = min_xyz[1] + height * 0.50
        y_nose_high = min_xyz[1] + height * 0.74
        z_face_front = min_xyz[2] + depth * 0.58
        z_nose_front = min_xyz[2] + depth * 0.68

        tip_center = np.array(
            [center[0], min_xyz[1] + height * 0.60, min_xyz[2] + depth * 0.84],
            dtype=np.float32,
        )
        bridge_center = np.array(
            [center[0], min_xyz[1] + height * 0.67, min_xyz[2] + depth * 0.74],
            dtype=np.float32,
        )
        alar_left_center = np.array(
            [center[0] - width * 0.055, min_xyz[1] + height * 0.58, min_xyz[2] + depth * 0.80],
            dtype=np.float32,
        )
        alar_right_center = np.array(
            [center[0] + width * 0.055, min_xyz[1] + height * 0.58, min_xyz[2] + depth * 0.80],
            dtype=np.float32,
        )
        columella_center = np.array(
            [center[0], min_xyz[1] + height * 0.54, min_xyz[2] + depth * 0.81],
            dtype=np.float32,
        )
        chin_center = np.array(
            [center[0], min_xyz[1] + height * 0.30, min_xyz[2] + depth * 0.63],
            dtype=np.float32,
        )
        left_jaw_center = np.array(
            [center[0] - width * 0.22, min_xyz[1] + height * 0.33, min_xyz[2] + depth * 0.54],
            dtype=np.float32,
        )
        right_jaw_center = np.array(
            [center[0] + width * 0.22, min_xyz[1] + height * 0.33, min_xyz[2] + depth * 0.54],
            dtype=np.float32,
        )

        changed_vertices = 0

        for i in range(len(v)):
            x, y, z = v[i]
            ox, oy, oz = float(x), float(y), float(z)

            if oy < y_neck_cut:
                continue

            side = -1.0 if ox < center[0] else 1.0

            face_front_gate = gate(oy, oz, y_min=y_lower_face_cut, z_min=z_face_front)

            nose_gate = gate(
                oy,
                oz,
                y_min=y_nose_low,
                y_max=y_nose_high,
                z_min=z_nose_front,
            )

            chin_gate = gate(
                oy,
                oz,
                y_min=min_xyz[1] + height * 0.22,
                y_max=min_xyz[1] + height * 0.40,
                z_min=min_xyz[2] + depth * 0.54,
            )

            jaw_gate = gate(
                oy,
                oz,
                y_min=min_xyz[1] + height * 0.24,
                y_max=min_xyz[1] + height * 0.42,
                z_min=min_xyz[2] + depth * 0.46,
                z_max=min_xyz[2] + depth * 0.70,
            )

            w_tip = ellipsoid_weight(
                ox, oy, oz,
                float(tip_center[0]), float(tip_center[1]), float(tip_center[2]),
                width * 0.045, height * 0.05, depth * 0.08,
            ) * nose_gate

            w_bridge = ellipsoid_weight(
                ox, oy, oz,
                float(bridge_center[0]), float(bridge_center[1]), float(bridge_center[2]),
                width * 0.04, height * 0.10, depth * 0.07,
            ) * nose_gate

            w_alar_l = ellipsoid_weight(
                ox, oy, oz,
                float(alar_left_center[0]), float(alar_left_center[1]), float(alar_left_center[2]),
                width * 0.05, height * 0.05, depth * 0.06,
            ) * nose_gate

            w_alar_r = ellipsoid_weight(
                ox, oy, oz,
                float(alar_right_center[0]), float(alar_right_center[1]), float(alar_right_center[2]),
                width * 0.05, height * 0.05, depth * 0.06,
            ) * nose_gate

            w_col = ellipsoid_weight(
                ox, oy, oz,
                float(columella_center[0]), float(columella_center[1]), float(columella_center[2]),
                width * 0.03, height * 0.05, depth * 0.06,
            ) * nose_gate

            w_chin = ellipsoid_weight(
                ox, oy, oz,
                float(chin_center[0]), float(chin_center[1]), float(chin_center[2]),
                width * 0.10, height * 0.08, depth * 0.10,
            ) * chin_gate * face_front_gate

            w_left_jaw = ellipsoid_weight(
                ox, oy, oz,
                float(left_jaw_center[0]), float(left_jaw_center[1]), float(left_jaw_center[2]),
                width * 0.08, height * 0.08, depth * 0.09,
            ) * jaw_gate

            w_right_jaw = ellipsoid_weight(
                ox, oy, oz,
                float(right_jaw_center[0]), float(right_jaw_center[1]), float(right_jaw_center[2]),
                width * 0.08, height * 0.08, depth * 0.09,
            ) * jaw_gate

            w_alar = max(w_alar_l, w_alar_r)

            moved = False

            if w_tip > 0.0:
                z += tip_projection * 0.030 * w_tip
                y -= tip_rotation * 0.018 * w_tip
                z += tip_rotation * 0.006 * w_tip
                moved = True

            if w_bridge > 0.0:
                z += bridge * 0.016 * w_bridge
                moved = True

            if w_alar > 0.0:
                x += side * alar_width * 0.012 * w_alar
                z += alar_width * 0.002 * w_alar
                moved = True

            if w_col > 0.0:
                y -= tip_rotation * 0.006 * w_col
                z += tip_projection * 0.006 * w_col
                moved = True

            if w_chin > 0.0:
                z += chin * 0.020 * w_chin
                y -= chin * 0.010 * w_chin
                moved = True

            if w_left_jaw > 0.0:
                x -= jaw * 0.012 * w_left_jaw
                z += jaw * 0.002 * w_left_jaw
                moved = True

            if w_right_jaw > 0.0:
                x += jaw * 0.012 * w_right_jaw
                z += jaw * 0.002 * w_right_jaw
                moved = True

            if moved:
                v[i] = [x, y, z]
                changed_vertices += 1

        logger.info(
            "Simulation mesh appliquée | src=%s | dst=%s | vertices=%d | modified=%d",
            src_obj,
            dst_obj,
            len(v),
            changed_vertices,
        )

        dst_obj.parent.mkdir(parents=True, exist_ok=True)
        with dst_obj.open("w", encoding="utf-8") as f:
            vi = 0
            for line in raw_lines:
                if line.startswith("v "):
                    x, y, z = v[vi]
                    f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
                    vi += 1
                else:
                    f.write(line)

    def _save_state(self, session_id: str, state: dict) -> None:
        p = self.sessions_dir / session_id / "state.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def _load_state(self, session_id: str) -> dict | None:
        p = self.sessions_dir / session_id / "state.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def _find_best_obj(self, root: Path) -> Path | None:
        candidates = [
            root / "input" / "input.obj",
            root / "input" / "input_detail.obj",
            root / "input.obj",
            root / "input_detail.obj",
        ]
        for p in candidates:
            if p.exists():
                logger.info("DECA selected OBJ = %s", p)
                return p.resolve()

        files = sorted(root.rglob("*.obj"))
        if files:
            logger.info("DECA fallback OBJ = %s", files[0])
            return files[0].resolve()
        return None

    def _find_best_mtl(self, obj_path: Path) -> Path | None:
        direct = obj_path.with_suffix(".mtl")
        if direct.exists():
            logger.info("DECA selected MTL = %s", direct)
            return direct.resolve()

        candidates = sorted(obj_path.parent.glob("*.mtl"))
        if candidates:
            logger.info("DECA fallback MTL = %s", candidates[0])
            return candidates[0].resolve()
        return None

    def _find_texture_near(self, obj_path: Path) -> Path | None:
        preferred = [
            obj_path.parent / "input.png",
            obj_path.parent / "input.jpg",
            obj_path.parent / "input.jpeg",
        ]
        for p in preferred:
            if p.exists():
                logger.info("DECA selected texture = %s", p)
                return p.resolve()

        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            cand = sorted(obj_path.parent.glob(f"*{ext}"))
            if cand:
                logger.info("DECA fallback texture = %s", cand[0])
                return cand[0].resolve()
        return None

    def _find_preview(self, root: Path) -> Path | None:
        preferred = [
            root / "input" / "input_vis.jpg",
            root / "input" / "input_vis_original_size.jpg",
            root / "input_vis.jpg",
            root / "input_vis_original_size.jpg",
        ]
        for p in preferred:
            if p.exists():
                return p.resolve()

        for ext in [".jpg", ".png"]:
            hits = sorted(root.rglob(f"*{ext}"))
            if hits:
                return hits[0].resolve()
        return None

    def _public_result(
        self,
        obj_path: Path,
        mtl_path: Path | None,
        texture_path: Path | None,
        preview_path: Path | None,
    ) -> dict:
        obj_url = "/" + str(obj_path.relative_to(self.output_root.parent)).replace("\\", "/")
        mtl_url = (
            "/" + str(mtl_path.relative_to(self.output_root.parent)).replace("\\", "/")
            if mtl_path and mtl_path.exists()
            else None
        )
        texture_url = (
            "/" + str(texture_path.relative_to(self.output_root.parent)).replace("\\", "/")
            if texture_path and texture_path.exists()
            else None
        )
        preview_url = (
            "/" + str(preview_path.relative_to(self.output_root.parent)).replace("\\", "/")
            if preview_path and preview_path.exists()
            else None
        )

        logger.info("PUBLIC OBJ URL = %s", obj_url)
        logger.info("PUBLIC MTL URL = %s", mtl_url)
        logger.info("PUBLIC TEX URL = %s", texture_url)
        logger.info("PUBLIC PREVIEW URL = %s", preview_url)

        return {
            "obj_url": obj_url,
            "mtl_url": mtl_url,
            "texture_url": texture_url,
            "preview_url": preview_url,
        }