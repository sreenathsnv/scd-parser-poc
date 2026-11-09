import React from "react";

const SEVERITY_COLOR = { error: "#c0392b", warning: "#d68910", info: "#2980b9" };

export default function ValidationPanel({ report }) {
  if (!report) {
    return <p style={{ color: "#888" }}>No validation report loaded yet.</p>;
  }
  return (
    <div>
      <p>
        <strong style={{ color: SEVERITY_COLOR.error }}>{report.error_count} errors</strong>
        {"  "}
        <strong style={{ color: SEVERITY_COLOR.warning }}>{report.warning_count} warnings</strong>
      </p>
      <p style={{ color: "#888", fontSize: 12 }}>
        sidecar: {report.sidecar?.status || "unknown"}
        {report.sidecar?.note ? ` — ${report.sidecar.note}` : ""}
      </p>
      <ul style={{ listStyle: "none", padding: 0, maxHeight: 500, overflowY: "auto" }}>
        {report.findings.map((f, i) => (
          <li
            key={i}
            style={{
              borderLeft: `4px solid ${SEVERITY_COLOR[f.severity] || "#888"}`,
              padding: "6px 10px",
              marginBottom: 4,
              background: "#f7f7f7",
            }}
          >
            <div style={{ fontSize: 11, color: "#888" }}>{f.rule} &middot; {f.path}</div>
            <div>{f.message}</div>
          </li>
        ))}
        {report.findings.length === 0 && <li style={{ color: "#888" }}>No findings.</li>}
      </ul>
    </div>
  );
}
