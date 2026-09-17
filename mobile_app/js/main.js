import {
  initViewer,
  loadObjWithMtl,
  setSurgeryParams,
  setDirectEditEnabled,
  setBrushRadius,
  setBrushStrength,
  undoLastEdit,
  resetAllEdits,
} from "./viewer.js?v=20260807";

import {
  reconstructFace,
  simulateFace,
  absoluteAssetUrl,
} from "./api.js?v=20260807";

const elements = {
  info: document.getElementById("info"),

  photoInput: document.getElementById("photoInput"),
  reconstructBtn: document.getElementById("reconstructBtn"),
  simulateBtn: document.getElementById("simulateBtn"),

  tipProjectionSlider: document.getElementById(
    "tipProjectionSlider"
  ),
  tipRotationSlider: document.getElementById(
    "tipRotationSlider"
  ),
  bridgeSlider: document.getElementById("bridgeSlider"),
  alarWidthSlider: document.getElementById("alarWidthSlider"),
  chinSlider: document.getElementById("chinSlider"),
  jawSlider: document.getElementById("jawSlider"),

  tipProjectionValue: document.getElementById(
    "tipProjectionValue"
  ),
  tipRotationValue: document.getElementById(
    "tipRotationValue"
  ),
  bridgeValue: document.getElementById("bridgeValue"),
  alarWidthValue: document.getElementById("alarWidthValue"),
  chinValue: document.getElementById("chinValue"),
  jawValue: document.getElementById("jawValue"),

  brushRadius: document.getElementById("brushRadius"),
  brushStrength: document.getElementById("brushStrength"),
  brushRadiusValue: document.getElementById(
    "brushRadiusValue"
  ),
  brushStrengthValue: document.getElementById(
    "brushStrengthValue"
  ),

  undoEditBtn: document.getElementById("undoEditBtn"),
  resetEditBtn: document.getElementById("resetEditBtn"),
};

const state = {
  sessionId: null,
  busy: false,
  previewTimer: null,
};

function setInfo(message, isError = false) {
  if (!elements.info) return;

  elements.info.textContent = message;
  elements.info.classList.toggle("error", isError);
}

function getNumber(element, fallback = 0) {
  if (!element) return fallback;

  const value = Number(element.value);

  return Number.isFinite(value) ? value : fallback;
}

function updateBackendValues() {
  if (elements.tipProjectionValue) {
    elements.tipProjectionValue.textContent =
      getNumber(elements.tipProjectionSlider).toFixed(2);
  }

  if (elements.tipRotationValue) {
    elements.tipRotationValue.textContent =
      getNumber(elements.tipRotationSlider).toFixed(2);
  }

  if (elements.bridgeValue) {
    elements.bridgeValue.textContent =
      getNumber(elements.bridgeSlider).toFixed(2);
  }

  if (elements.alarWidthValue) {
    elements.alarWidthValue.textContent =
      getNumber(elements.alarWidthSlider).toFixed(2);
  }

  if (elements.chinValue) {
    elements.chinValue.textContent =
      getNumber(elements.chinSlider).toFixed(2);
  }

  if (elements.jawValue) {
    elements.jawValue.textContent =
      getNumber(elements.jawSlider).toFixed(2);
  }
}

function updateBrushValues() {
  const radius = getNumber(elements.brushRadius, 0.055);
  const strength = getNumber(elements.brushStrength, 0.65);

  if (elements.brushRadiusValue) {
    elements.brushRadiusValue.textContent =
      radius.toFixed(3);
  }

  if (elements.brushStrengthValue) {
    elements.brushStrengthValue.textContent =
      strength.toFixed(2);
  }
}

function setControlsEnabled(enabled) {
  const controls = [
    elements.simulateBtn,

    elements.tipProjectionSlider,
    elements.tipRotationSlider,
    elements.bridgeSlider,
    elements.alarWidthSlider,
    elements.chinSlider,
    elements.jawSlider,

    elements.brushRadius,
    elements.brushStrength,

    elements.undoEditBtn,
    elements.resetEditBtn,
  ];

  controls.forEach((control) => {
    if (control) {
      control.disabled = !enabled;
    }
  });

  setDirectEditEnabled(enabled);
}

function resetBackendSliders() {
  const sliders = [
    elements.tipProjectionSlider,
    elements.tipRotationSlider,
    elements.bridgeSlider,
    elements.alarWidthSlider,
    elements.chinSlider,
    elements.jawSlider,
  ];

  sliders.forEach((slider) => {
    if (slider) {
      slider.value = "0";
    }
  });

  updateBackendValues();
  applyBackendParameters();
}

function applyBackendParameters() {
  setSurgeryParams({
    tipProjection: getNumber(
      elements.tipProjectionSlider
    ),
    tipRotation: getNumber(
      elements.tipRotationSlider
    ),
    bridge: getNumber(elements.bridgeSlider),
    alarWidth: getNumber(elements.alarWidthSlider),
    chin: getNumber(elements.chinSlider),
    jaw: getNumber(elements.jawSlider),
  });
}

function configureBrush() {
  const radius = getNumber(elements.brushRadius, 0.055);
  const strength = getNumber(
    elements.brushStrength,
    0.65
  );

  setBrushRadius(radius);
  setBrushStrength(strength);
  updateBrushValues();
}

function getSimulationPayload() {
  return {
    sessionId: state.sessionId,
    tipProjection: getNumber(
      elements.tipProjectionSlider
    ),
    tipRotation: getNumber(
      elements.tipRotationSlider
    ),
    bridge: getNumber(elements.bridgeSlider),
    alarWidth: getNumber(elements.alarWidthSlider),
    chin: getNumber(elements.chinSlider),
    jaw: getNumber(elements.jawSlider),
  };
}

function scheduleBackendPreview() {
  updateBackendValues();

  clearTimeout(state.previewTimer);

  state.previewTimer = setTimeout(() => {
    if (!state.sessionId) return;

    applyBackendParameters();

    setInfo(
      "Paramètres modifiés. Cliquez sur Simulation backend pour générer le nouveau mesh."
    );
  }, 100);
}

async function reconstruct() {
  if (state.busy) return;

  const file = elements.photoInput?.files?.[0];

  if (!file) {
    setInfo(
      "Sélectionnez une photo avant de reconstruire.",
      true
    );
    return;
  }

  if (!file.type.startsWith("image/")) {
    setInfo(
      "Le fichier sélectionné doit être une image.",
      true
    );
    return;
  }

  state.busy = true;
  state.sessionId = null;

  setControlsEnabled(false);
  setInfo("Reconstruction DECA en cours...");

  try {
    const result = await reconstructFace(file);

    if (!result?.ok) {
      throw new Error("La reconstruction DECA a échoué.");
    }

    if (!result.session_id) {
      throw new Error("Session DECA absente.");
    }

    if (!result.obj_url) {
      throw new Error("URL OBJ absente.");
    }

    state.sessionId = result.session_id;

    const objUrl = absoluteAssetUrl(
      result.obj_url
    );

    const mtlUrl = absoluteAssetUrl(
      result.mtl_url
    );

    await loadObjWithMtl(
      objUrl,
      mtlUrl,
      "info"
    );

    resetBackendSliders();
    configureBrush();
    resetAllEdits();

    setControlsEnabled(true);

    setInfo(
      "Modèle chargé. Cliquez sur le visage pour placer le target."
    );
  } catch (error) {
    console.error("Erreur reconstruction:", error);

    state.sessionId = null;
    setControlsEnabled(false);

    setInfo(
      error.message ||
        "Erreur pendant la reconstruction.",
      true
    );
  } finally {
    state.busy = false;
  }
}

async function simulateBackend() {
  if (state.busy) return;

  if (!state.sessionId) {
    setInfo(
      "Reconstruisez d'abord le visage.",
      true
    );
    return;
  }

  state.busy = true;

  setControlsEnabled(false);
  setInfo("Simulation backend en cours...");

  try {
    const result = await simulateFace(
      getSimulationPayload()
    );

    if (!result?.ok) {
      throw new Error("La simulation backend a échoué.");
    }

    if (!result.obj_url) {
      throw new Error("OBJ simulé absent.");
    }

    const objUrl = absoluteAssetUrl(
      result.obj_url
    );

    const mtlUrl = absoluteAssetUrl(
      result.mtl_url
    );

    await loadObjWithMtl(
      objUrl,
      mtlUrl,
      "info"
    );

    resetAllEdits();
    configureBrush();

    setControlsEnabled(true);

    setInfo(
      "Simulation terminée. Cliquez sur une zone puis faites-la glisser."
    );
  } catch (error) {
    console.error("Erreur simulation:", error);

    setControlsEnabled(true);

    setInfo(
      error.message ||
        "Erreur pendant la simulation.",
      true
    );
  } finally {
    state.busy = false;
  }
}

function photoChanged() {
  state.sessionId = null;

  resetAllEdits();
  setControlsEnabled(false);

  setInfo(
    "Photo sélectionnée. Cliquez sur Reconstruire."
  );
}

function bindEvents() {
  elements.reconstructBtn?.addEventListener(
    "click",
    reconstruct
  );

  elements.simulateBtn?.addEventListener(
    "click",
    simulateBackend
  );

  elements.photoInput?.addEventListener(
    "change",
    photoChanged
  );

  const backendSliders = [
    elements.tipProjectionSlider,
    elements.tipRotationSlider,
    elements.bridgeSlider,
    elements.alarWidthSlider,
    elements.chinSlider,
    elements.jawSlider,
  ];

  backendSliders.forEach((slider) => {
    slider?.addEventListener(
      "input",
      scheduleBackendPreview
    );
  });

  elements.brushRadius?.addEventListener(
    "input",
    () => {
      configureBrush();
      setInfo("Rayon de modification mis à jour.");
    }
  );

  elements.brushStrength?.addEventListener(
    "input",
    () => {
      configureBrush();
      setInfo("Intensité de modification mise à jour.");
    }
  );

  elements.undoEditBtn?.addEventListener(
    "click",
    () => {
      undoLastEdit();
      setInfo("Dernière modification annulée.");
    }
  );

  elements.resetEditBtn?.addEventListener(
    "click",
    () => {
      resetAllEdits();
      setInfo(
        "Modifications locales réinitialisées."
      );
    }
  );
}

function bootstrap() {
  initViewer("viewer", "info");

  bindEvents();

  updateBackendValues();
  updateBrushValues();

  setControlsEnabled(false);

  setInfo(
    "Chargez une photo puis lancez la reconstruction."
  );
}

bootstrap();