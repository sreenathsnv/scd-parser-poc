const BASE = "/api";

// Imported files live at "imported/<name>" -- encodeURIComponent alone would
// turn the "/" into "%2F", which the backend's path-type route parameter
// won't treat as a separator. Encode each segment, keep the "/" literal.
function encodeFilePath(name) {
  return name.split("/").map(encodeURIComponent).join("/");
}

async function req(path, options) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${options?.method || "GET"} ${path} -> ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  health: () => req("/health"),
  listFiles: () => req("/files"),
  parseFile: (name) => req(`/files/${encodeFilePath(name)}/parse`, { method: "POST" }),
  getTree: (name) => req(`/files/${encodeFilePath(name)}/tree`),
  getGraphView: (name) => req(`/files/${encodeFilePath(name)}/graph-view`),
  graphLoad: (name) => req(`/files/${encodeFilePath(name)}/graph-load`, { method: "POST" }),
  validate: (name) => req(`/files/${encodeFilePath(name)}/validate`),
  editDai: (name, body) =>
    req(`/files/${encodeFilePath(name)}/edit/dai`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  saveAsCopy: (name, newName) =>
    req(`/files/${encodeFilePath(name)}/save-as-copy?new_filename=${encodeURIComponent(newName)}`, { method: "POST" }),
  saveOverwrite: (name) =>
    req(`/files/${encodeFilePath(name)}/save-overwrite?confirm=true`, { method: "POST" }),
  importFile: async (file) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/files/import`, { method: "POST", body: form });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`POST /files/import -> ${res.status}: ${text}`);
    }
    return res.json();
  },
};
