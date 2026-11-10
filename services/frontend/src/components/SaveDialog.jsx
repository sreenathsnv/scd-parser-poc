import React, { useState } from "react";

const backdropStyle = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
  display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
};
const boxStyle = {
  background: "#fff", borderRadius: 6, padding: 20, width: 420, boxShadow: "0 4px 24px rgba(0,0,0,0.2)",
};

export function SaveAsCopyDialog({ suggestedName, onConfirm, onCancel }) {
  const [name, setName] = useState(suggestedName);
  return (
    <div style={backdropStyle}>
      <div style={boxStyle}>
        <h3 style={{ marginTop: 0 }}>Save as copy</h3>
        <p style={{ fontSize: 13, color: "#666" }}>The original file will not be modified.</p>
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ width: "100%", padding: 6, fontFamily: "monospace", boxSizing: "border-box" }}
        />
        <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end", gap: 8 }}>
          <button onClick={onCancel}>Cancel</button>
          <button onClick={() => onConfirm(name)} disabled={!name.trim()}>
            Save copy
          </button>
        </div>
      </div>
    </div>
  );
}

export function OverwriteConfirmDialog({ filename, onConfirm, onCancel }) {
  return (
    <div style={backdropStyle}>
      <div style={boxStyle}>
        <h3 style={{ marginTop: 0, color: "#c0392b" }}>Overwrite original file?</h3>
        <p style={{ fontSize: 13 }}>
          This will overwrite the original file on disk and <strong>cannot be undone</strong>:
        </p>
        <p style={{ fontFamily: "monospace", background: "#f5f5f5", padding: 8, wordBreak: "break-all" }}>
          {filename}
        </p>
        <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end", gap: 8 }}>
          <button onClick={onCancel}>Cancel</button>
          <button onClick={onConfirm} style={{ background: "#c0392b", color: "#fff", border: "none", padding: "6px 12px" }}>
            Overwrite
          </button>
        </div>
      </div>
    </div>
  );
}
