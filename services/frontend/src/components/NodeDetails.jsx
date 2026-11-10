import React, { useEffect, useState } from "react";

const HIDDEN_KEYS = new Set(["iedName", "ldInst", "lnPrefix", "lnClass", "lnInst", "doiPath", "daiName", "editable"]);

export default function NodeDetails({ node, onSaveDai, saving, saveError }) {
  const [draft, setDraft] = useState("");

  useEffect(() => {
    setDraft(node?.attrs?.val ?? "");
  }, [node]);

  if (!node) {
    return <p style={{ color: "#888" }}>Select a node in the tree to see its details.</p>;
  }

  const entries = Object.entries(node.attrs || {}).filter(
    ([k, v]) => v !== null && v !== undefined && !HIDDEN_KEYS.has(k)
  );
  const editable = node.kind === "DataAttribute" && node.attrs?.editable;
  const dirty = editable && draft !== (node.attrs?.val ?? "");

  return (
    <div>
      <h3 style={{ marginBottom: 4 }}>{node.label}</h3>
      <p style={{ color: "#888", marginTop: 0 }}>{node.kind}</p>

      {editable && (
        <div style={{ marginBottom: 12 }}>
          <label style={{ fontSize: 12, color: "#666" }}>value</label>
          <div style={{ display: "flex", gap: 6 }}>
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              style={{ flex: 1, fontFamily: "monospace", padding: 4 }}
            />
            <button disabled={!dirty || saving} onClick={() => onSaveDai(node, draft)}>
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
          {saveError && <p style={{ color: "crimson", fontSize: 12 }}>{saveError}</p>}
        </div>
      )}

      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <tbody>
          {entries.map(([k, v]) => (
            <tr key={k}>
              <td style={{ padding: "4px 8px", color: "#666", verticalAlign: "top", whiteSpace: "nowrap" }}>{k}</td>
              <td style={{ padding: "4px 8px", fontFamily: "monospace" }}>{String(v)}</td>
            </tr>
          ))}
          {entries.length === 0 && !editable && (
            <tr>
              <td style={{ padding: "4px 8px", color: "#888" }}>(no attributes)</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
