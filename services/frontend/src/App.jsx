import React, { useEffect, useState } from "react";

// Phase 0 placeholder; Explorer UI (tree/graph/editor) lands in Phase 1.
export default function App() {
  const [health, setHealth] = useState("checking...");
  const [files, setFiles] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((data) => setHealth(data.status))
      .catch((e) => setHealth(`unreachable (${e.message})`));

    fetch("/api/files")
      .then((r) => r.json())
      .then((data) => setFiles(data))
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", padding: "2rem", maxWidth: 720 }}>
      <h1>SCL Explorer</h1>
      <p style={{ color: "#666" }}>
        Phase 0 foundations: parser/serializer, custom validation rules, Neo4j ingestion and this
        gateway are wired up. The tree/graph/editor views land in Phase 1.
      </p>
      <h2>api-gateway status</h2>
      <p>
        <code>GET /api/health</code> &rarr; <strong>{health}</strong>
      </p>
      <h2>Files on server (SCD_FILES_DIR)</h2>
      {error && <p style={{ color: "crimson" }}>Error: {error}</p>}
      {files && (
        <>
          <p>
            <code>{files.filesDir}</code>
          </p>
          <ul>
            {files.files.length === 0 && <li>(none found)</li>}
            {files.files.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
