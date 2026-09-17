const API_BASE = "http://127.0.0.1:8000";

async function parseResponse(res) {
  let data = null;

  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const message =
      data?.detail ||
      data?.error ||
      `HTTP ${res.status} ${res.statusText}`;
    throw new Error(message);
  }

  return data;
}

export function absoluteAssetUrl(path) {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_BASE}${path}`;
}

export async function reconstructFace(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/reconstruct`, {
    method: "POST",
    body: formData,
  });

  return parseResponse(res);
}

export async function simulateFace({
  sessionId,
  tipProjection,
  tipRotation,
  bridge,
  alarWidth,
  chin,
  jaw,
}) {
  const res = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      tipProjection,
      tipRotation,
      bridge,
      alarWidth,
      chin,
      jaw,
    }),
  });

  return parseResponse(res);
}