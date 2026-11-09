import React from "react";

export default function NodeDetails({ node }) {
  if (!node) {
    return <p style={{ color: "#888" }}>Select a node in the tree to see its details.</p>;
  }
  const entries = Object.entries(node.attrs || {}).filter(([, v]) => v !== null && v !== undefined);
  return (
    <div>
      <h3 style={{ marginBottom: 4 }}>{node.label}</h3>
      <p style={{ color: "#888", marginTop: 0 }}>{node.kind}</p>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <tbody>
          {entries.map(([k, v]) => (
            <tr key={k}>
              <td style={{ padding: "4px 8px", color: "#666", verticalAlign: "top", whiteSpace: "nowrap" }}>{k}</td>
              <td style={{ padding: "4px 8px", fontFamily: "monospace" }}>{String(v)}</td>
            </tr>
          ))}
          {entries.length === 0 && (
            <tr>
              <td style={{ padding: "4px 8px", color: "#888" }}>(no attributes)</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
