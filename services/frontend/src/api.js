const BASE = "/api";

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
  parseFile: (name) => req(`/files/${encodeURIComponent(name)}/parse`, { method: "POST" }),
  getTree: (name) => req(`/files/${encodeURIComponent(name)}/tree`),
  validate: (name) => req(`/files/${encodeURIComponent(name)}/validate`),
  saveAsCopy: (name, newName) =>
    req(`/files/${encodeURIComponent(name)}/save-as-copy?new_filename=${encodeURIComponent(newName)}`, { method: "POST" }),
  saveOverwrite: (name) =>
    req(`/files/${encodeURIComponent(name)}/save-overwrite?confirm=true`, { method: "POST" }),
};
