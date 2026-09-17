import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { MTLLoader } from "three/addons/loaders/MTLLoader.js";

let scene = null;
let camera = null;
let renderer = null;
let controls = null;
let container = null;

let currentModel = null;
let targetMarker = null;

let raycaster = null;
let pointer = null;

let selectedMesh = null;
let selectedPoint = null;
let isDragging = false;
let directEditEnabled = false;

let brushRadius = 0.055;
let brushStrength = 0.65;

const originalGeometry = new WeakMap();

let editOperations = [];

const surgeryState = {
  tipProjection: 0,
  tipRotation: 0,
  bridge: 0,
  alarWidth: 0,
  chin: 0,
  jaw: 0,
};

export function initViewer(
  containerId,
  infoId = "info"
) {
  container = document.getElementById(
    containerId
  );

  if (!container) {
    throw new Error(
      `Container introuvable: #${containerId}`
    );
  }

  scene = new THREE.Scene();
  scene.background = new THREE.Color(
    0xf5f7fa
  );

  camera = new THREE.PerspectiveCamera(
    45,
    Math.max(container.clientWidth, 1) /
      Math.max(container.clientHeight, 1),
    0.01,
    5000
  );

  camera.position.set(0, 0, 180);

  renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: false,
    preserveDrawingBuffer: true,
  });

  renderer.setPixelRatio(
    Math.min(
      window.devicePixelRatio || 1,
      2
    )
  );

  renderer.setSize(
    Math.max(container.clientWidth, 1),
    Math.max(container.clientHeight, 1)
  );

  renderer.domElement.style.display = "block";
  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";
  renderer.domElement.style.touchAction = "none";
  renderer.domElement.style.cursor = "crosshair";

  container.innerHTML = "";
  container.appendChild(renderer.domElement);

  raycaster = new THREE.Raycaster();
  pointer = new THREE.Vector2();

  controls = new OrbitControls(
    camera,
    renderer.domElement
  );

  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.target.set(0, 0, 0);

  addLights();
  createTargetMarker();

  renderer.domElement.addEventListener(
    "pointerdown",
    onPointerDown,
    { passive: false }
  );

  renderer.domElement.addEventListener(
    "pointermove",
    onPointerMove,
    { passive: false }
  );

  renderer.domElement.addEventListener(
    "pointerup",
    onPointerUp,
    { passive: false }
  );

  renderer.domElement.addEventListener(
    "pointercancel",
    onPointerUp,
    { passive: false }
  );

  renderer.domElement.addEventListener(
    "click",
    onCanvasClick,
    { passive: false }
  );

  window.addEventListener(
    "resize",
    onResize
  );

  animate();

  setInfo(
    infoId,
    "Viewer prêt. Chargez une reconstruction."
  );
}

export async function loadObjWithMtl(
  objUrl,
  mtlUrl,
  infoId = "info"
) {
  if (!scene) {
    throw new Error(
      "initViewer() doit être appelé avant le chargement."
    );
  }

  if (!objUrl) {
    throw new Error("URL OBJ manquante.");
  }

  clearViewer();

  setInfo(
    infoId,
    "Chargement du modèle 3D..."
  );

  if (!mtlUrl) {
    return loadObjOnly(objUrl, infoId);
  }

  const objBase = getBasePath(objUrl);
  const objFile = getFileName(objUrl);

  const mtlBase = getBasePath(mtlUrl);
  const mtlFile = getFileName(mtlUrl);

  return new Promise((resolve, reject) => {
    const mtlLoader = new MTLLoader();

    mtlLoader.setPath(mtlBase);
    mtlLoader.setResourcePath(mtlBase);

    mtlLoader.load(
      mtlFile,
      (materials) => {
        try {
          materials.preload();

          const objLoader = new OBJLoader();

          objLoader.setPath(objBase);
          objLoader.setMaterials(materials);

          objLoader.load(
            objFile,
            (object) => {
              finishLoad(
                object,
                infoId,
                false
              );

              resolve(object);
            },
            undefined,
            (error) => {
              console.warn(
                "OBJ + MTL échoué. Fallback OBJ-only.",
                error
              );

              loadObjOnly(objUrl, infoId)
                .then(resolve)
                .catch(reject);
            }
          );
        } catch (error) {
          console.warn(
            "Préparation MTL échouée.",
            error
          );

          loadObjOnly(objUrl, infoId)
            .then(resolve)
            .catch(reject);
        }
      },
      undefined,
      (error) => {
        console.warn(
          "Chargement MTL échoué.",
          error
        );

        loadObjOnly(objUrl, infoId)
          .then(resolve)
          .catch(reject);
      }
    );
  });
}

export function setDirectEditEnabled(
  enabled
) {
  directEditEnabled = Boolean(enabled);

  console.log(
    "ÉDITION LOCALE:",
    directEditEnabled
      ? "ACTIVE"
      : "INACTIVE"
  );
}

export function setBrushRadius(value) {
  brushRadius = Math.max(
    0.005,
    Number(value) || 0.055
  );
}

export function setBrushStrength(value) {
  brushStrength = Math.max(
    0.01,
    Math.min(
      2,
      Number(value) || 0.65
    )
  );
}

export function setSurgeryParams(
  params = {}
) {
  surgeryState.tipProjection =
    Number(params.tipProjection) || 0;

  surgeryState.tipRotation =
    Number(params.tipRotation) || 0;

  surgeryState.bridge =
    Number(params.bridge) || 0;

  surgeryState.alarWidth =
    Number(params.alarWidth) || 0;

  surgeryState.chin =
    Number(params.chin) || 0;

  surgeryState.jaw =
    Number(params.jaw) || 0;

  /*
   * Ces valeurs sont envoyées au backend.
   * L’édition locale se fait par target.
   */
}

export function undoLastEdit() {
  if (!editOperations.length) {
    return;
  }

  editOperations.pop();
  rebuildAllEdits();
}

export function resetAllEdits() {
  editOperations = [];
  rebuildAllEdits();
  hideTarget();
}

export function getSelectedPoint() {
  if (!selectedPoint) {
    return null;
  }

  return {
    x: selectedPoint.x,
    y: selectedPoint.y,
    z: selectedPoint.z,
  };
}

function loadObjOnly(objUrl, infoId) {
  return new Promise((resolve, reject) => {
    const loader = new OBJLoader();

    loader.load(
      objUrl,
      (object) => {
        finishLoad(
          object,
          infoId,
          true
        );

        resolve(object);
      },
      undefined,
      (error) => {
        console.error(
          "Erreur chargement OBJ:",
          error
        );

        setInfo(
          infoId,
          "Erreur chargement OBJ."
        );

        reject(error);
      }
    );
  });
}

function finishLoad(
  object,
  infoId,
  debugMaterial
) {
  let meshCount = 0;

  object.traverse((child) => {
    if (
      !child.isMesh ||
      !child.geometry?.attributes?.position
    ) {
      return;
    }

    meshCount += 1;

    const geometry = child.geometry;

    geometry.computeVertexNormals();

    originalGeometry.set(
      geometry,
      Float32Array.from(
        geometry.attributes.position.array
      )
    );

    if (debugMaterial) {
      child.material =
        new THREE.MeshNormalMaterial({
          side: THREE.DoubleSide,
        });
    } else {
      prepareMaterial(child);
    }
  });

  if (meshCount === 0) {
    throw new Error(
      "Aucun mesh valide trouvé dans l’OBJ."
    );
  }

  fitObjectToView(object);

  scene.add(object);
  currentModel = object;

  scene.updateMatrixWorld(true);
  camera.updateMatrixWorld(true);

  console.log(
    "Meshes chargés:",
    meshCount
  );

  setInfo(
    infoId,
    "Modèle chargé. Cliquez sur le visage."
  );
}

function prepareMaterial(mesh) {
  if (Array.isArray(mesh.material)) {
    mesh.material.forEach((material) => {
      if (!material) return;

      material.side = THREE.DoubleSide;
      material.needsUpdate = true;
    });

    return;
  }

  if (mesh.material) {
    mesh.material.side =
      THREE.DoubleSide;

    mesh.material.needsUpdate = true;
    return;
  }

  mesh.material =
    new THREE.MeshNormalMaterial({
      side: THREE.DoubleSide,
    });
}

function addLights() {
  scene.add(
    new THREE.AmbientLight(
      0xffffff,
      1.35
    )
  );

  const keyLight =
    new THREE.DirectionalLight(
      0xffffff,
      1.2
    );

  keyLight.position.set(
    120,
    120,
    150
  );

  scene.add(keyLight);

  const fillLight =
    new THREE.DirectionalLight(
      0xffffff,
      0.8
    );

  fillLight.position.set(
    -120,
    60,
    100
  );

  scene.add(fillLight);

  const rimLight =
    new THREE.DirectionalLight(
      0xffffff,
      0.45
    );

  rimLight.position.set(
    0,
    -100,
    120
  );

  scene.add(rimLight);
}

function createTargetMarker() {
  const point = new THREE.Mesh(
    new THREE.SphereGeometry(
      0.012,
      20,
      20
    ),
    new THREE.MeshBasicMaterial({
      color: 0xff244f,
      depthTest: false,
      transparent: true,
      opacity: 1,
    })
  );

  const ring = new THREE.Mesh(
    new THREE.RingGeometry(
      0.018,
      0.024,
      32
    ),
    new THREE.MeshBasicMaterial({
      color: 0xffffff,
      side: THREE.DoubleSide,
      depthTest: false,
      transparent: true,
      opacity: 1,
    })
  );

  targetMarker = new THREE.Group();

  targetMarker.add(point);
  targetMarker.add(ring);

  targetMarker.visible = false;
  targetMarker.renderOrder = 1000;

  point.renderOrder = 1000;
  ring.renderOrder = 1001;

  scene.add(targetMarker);
}

function onCanvasClick(event) {
  if (!directEditEnabled) {
    console.warn(
      "Édition locale inactive."
    );

    return;
  }

  if (!currentModel) {
    console.warn(
      "Aucun modèle chargé."
    );

    return;
  }

  updatePointer(event);

  scene.updateMatrixWorld(true);
  camera.updateMatrixWorld(true);

  raycaster.setFromCamera(
    pointer,
    camera
  );

  const hits = raycaster
    .intersectObject(
      currentModel,
      true
    )
    .filter(
      (hit) =>
        hit.object?.isMesh &&
        hit.object.geometry?.attributes
          ?.position
    );

  console.log(
    "Clic viewer:",
    {
      x: pointer.x,
      y: pointer.y,
      intersections: hits.length,
    }
  );

  if (!hits.length) {
    console.warn(
      "Aucune intersection avec le visage."
    );

    return;
  }

  const hit = hits[0];

  selectedMesh = hit.object;

  selectedPoint =
    selectedMesh.worldToLocal(
      hit.point.clone()
    );

  showTarget(hit.point);

  setInfo(
    "info",
    "Zone sélectionnée. Faites glisser la souris."
  );

  console.log(
    "Target sélectionné:",
    selectedPoint
  );
}

function onPointerDown(event) {
  if (!directEditEnabled) {
    return;
  }

  if (!currentModel) {
    return;
  }

  updatePointer(event);

  scene.updateMatrixWorld(true);
  camera.updateMatrixWorld(true);

  raycaster.setFromCamera(
    pointer,
    camera
  );

  const hits = raycaster
    .intersectObject(
      currentModel,
      true
    )
    .filter(
      (hit) =>
        hit.object?.isMesh &&
        hit.object.geometry?.attributes
          ?.position
    );

  console.log(
    "Pointer down:",
    hits.length
  );

  if (!hits.length) {
    return;
  }

  const hit = hits[0];

  selectedMesh = hit.object;

  selectedPoint =
    selectedMesh.worldToLocal(
      hit.point.clone()
    );

  showTarget(hit.point);

  isDragging = true;
  controls.enabled = false;

  renderer.domElement.setPointerCapture?.(
    event.pointerId
  );
}

function onPointerMove(event) {
  if (
    !isDragging ||
    !selectedMesh ||
    !selectedPoint ||
    !currentModel
  ) {
    return;
  }

  event.preventDefault();

  updatePointer(event);

  scene.updateMatrixWorld(true);
  camera.updateMatrixWorld(true);

  raycaster.setFromCamera(
    pointer,
    camera
  );

  const hits = raycaster
    .intersectObject(
      currentModel,
      true
    )
    .filter(
      (hit) =>
        hit.object === selectedMesh
    );

  if (!hits.length) {
    return;
  }

  const hit = hits[0];

  const currentLocalPoint =
    selectedMesh.worldToLocal(
      hit.point.clone()
    );

  const delta =
    currentLocalPoint
      .clone()
      .sub(selectedPoint);

  if (delta.lengthSq() < 0.0000001) {
    return;
  }

  editOperations.push({
    mesh: selectedMesh,
    center: selectedPoint.clone(),
    delta: delta.multiplyScalar(
      brushStrength
    ),
    radius: brushRadius,
  });

  selectedPoint.copy(
    currentLocalPoint
  );

  showTarget(hit.point);
  rebuildAllEdits();
}

function onPointerUp(event) {
  if (!isDragging) {
    return;
  }

  isDragging = false;

  if (controls) {
    controls.enabled = true;
  }

  renderer.domElement.releasePointerCapture?.(
    event.pointerId
  );
}

function updatePointer(event) {
  const rect =
    renderer.domElement.getBoundingClientRect();

  if (!rect.width || !rect.height) {
    return;
  }

  pointer.x =
    ((event.clientX - rect.left) /
      rect.width) *
      2 -
    1;

  pointer.y =
    -(
      ((event.clientY - rect.top) /
        rect.height) *
        2 -
      1
    );

  console.log(
    "Pointer NDC:",
    pointer.x,
    pointer.y
  );
}

function showTarget(worldPoint) {
  if (!targetMarker) {
    return;
  }

  targetMarker.visible = true;
  targetMarker.position.copy(
    worldPoint
  );

  const distance =
    camera.position.distanceTo(
      worldPoint
    );

  const markerSize = Math.max(
    distance * 0.018,
    0.02
  );

  targetMarker.scale.setScalar(
    markerSize
  );

  targetMarker.lookAt(
    camera.position
  );
}

function hideTarget() {
  if (targetMarker) {
    targetMarker.visible = false;
  }

  selectedMesh = null;
  selectedPoint = null;
  isDragging = false;

  if (controls) {
    controls.enabled = true;
  }
}

function rebuildAllEdits() {
  if (!currentModel) {
    return;
  }

  currentModel.traverse((mesh) => {
    if (
      !mesh.isMesh ||
      !mesh.geometry?.attributes?.position
    ) {
      return;
    }

    const geometry = mesh.geometry;
    const position =
      geometry.attributes.position;

    const original =
      originalGeometry.get(
        geometry
      );

    if (!original) {
      return;
    }

    position.array.set(original);

    editOperations.forEach(
      (operation) => {
        if (operation.mesh !== mesh) {
          return;
        }

        applyBrushOperation(
          position,
          original,
          operation.center,
          operation.delta,
          operation.radius
        );
      }
    );

    position.needsUpdate = true;
    geometry.computeVertexNormals();
  });
}

function applyBrushOperation(
  position,
  original,
  center,
  delta,
  radius
) {
  const radiusSquared =
    radius * radius;

  for (
    let index = 0;
    index < position.count;
    index += 1
  ) {
    const ox =
      original[index * 3];

    const oy =
      original[index * 3 + 1];

    const oz =
      original[index * 3 + 2];

    const dx = ox - center.x;
    const dy = oy - center.y;
    const dz = oz - center.z;

    const distanceSquared =
      dx * dx +
      dy * dy +
      dz * dz;

    if (
      distanceSquared >=
      radiusSquared
    ) {
      continue;
    }

    const distance = Math.sqrt(
      distanceSquared
    );

    const normalizedDistance =
      distance / radius;

    const influence = smoothFalloff(
      1 - normalizedDistance
    );

    position.setXYZ(
      index,
      position.getX(index) +
        delta.x * influence,
      position.getY(index) +
        delta.y * influence,
      position.getZ(index) +
        delta.z * influence
    );
  }
}

function smoothFalloff(value) {
  const t = Math.max(
    0,
    Math.min(1, value)
  );

  return t * t * (3 - 2 * t);
}

function clearViewer() {
  if (!currentModel || !scene) {
    return;
  }

  scene.remove(currentModel);

  currentModel.traverse((child) => {
    if (!child.isMesh) {
      return;
    }

    child.geometry?.dispose();

    if (Array.isArray(child.material)) {
      child.material.forEach(
        disposeMaterial
      );
    } else {
      disposeMaterial(child.material);
    }
  });

  currentModel = null;
  selectedMesh = null;
  selectedPoint = null;
  editOperations = [];

  if (renderer?.renderLists) {
    renderer.renderLists.dispose();
  }
}

function disposeMaterial(material) {
  if (!material) {
    return;
  }

  for (const key of Object.keys(material)) {
    const value = material[key];

    if (
      value?.isTexture &&
      typeof value.dispose === "function"
    ) {
      value.dispose();
    }
  }

  material.dispose?.();
}

function fitObjectToView(object) {
  const box = new THREE.Box3()
    .setFromObject(object);

  const center = box.getCenter(
    new THREE.Vector3()
  );

  const size = box.getSize(
    new THREE.Vector3()
  );

  object.position.sub(center);

  const maxDimension = Math.max(
    size.x,
    size.y,
    size.z
  );

  const scale =
    maxDimension > 0
      ? 140 / maxDimension
      : 1;

  object.scale.setScalar(scale);

  const scaledBox = new THREE.Box3()
    .setFromObject(object);

  const scaledSize =
    scaledBox.getSize(
      new THREE.Vector3()
    );

  const scaledMax = Math.max(
    scaledSize.x,
    scaledSize.y,
    scaledSize.z
  );

  const fovRadians =
    (camera.fov * Math.PI) / 180;

  const cameraZ =
    Math.abs(
      (scaledMax / 2) /
        Math.tan(fovRadians / 2)
    ) * 1.6;

  camera.position.set(
    0,
    0,
    cameraZ
  );

  camera.near = Math.max(
    0.01,
    cameraZ / 100
  );

  camera.far = cameraZ * 20;

  camera.updateProjectionMatrix();

  controls.target.set(0, 0, 0);
  controls.minDistance = cameraZ * 0.35;
  controls.maxDistance = cameraZ * 5;
  controls.update();
}

function getBasePath(url) {
  return url.substring(
    0,
    url.lastIndexOf("/") + 1
  );
}

function getFileName(url) {
  return url.substring(
    url.lastIndexOf("/") + 1
  );
}

function setInfo(infoId, message) {
  const element =
    document.getElementById(infoId);

  if (element) {
    element.textContent = message;
  }
}

function onResize() {
  if (!container || !camera || !renderer) {
    return;
  }

  const width =
    container.clientWidth || 1;

  const height =
    container.clientHeight || 1;

  camera.aspect = width / height;
  camera.updateProjectionMatrix();

  renderer.setSize(
    width,
    height
  );
}

function animate() {
  requestAnimationFrame(animate);

  controls?.update();
  renderer?.render(scene, camera);
}