import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import TreeView from "./components/TreeView";
import NodeDetails from "./components/NodeDetails";
import ValidationPanel from "./components/ValidationPanel";

export default function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [tree, setTree] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [report, setReport] = useState(null);
  const [tab, setTab] = useState("tree");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listFiles().then((d) => setFiles(d.files)).catch((e) => setError(e.message));
  }, []);

  async function openFile(name) {
    setError(null);
    setLoading(true);
    setSelectedFile(name);
    setSelectedNode(null);
    try {
      await api.parseFile(name);
      const [t, v] = await Promise.all([api.getTree(name), api.validate(name)]);
      setTree(t);
      setReport(v);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const treeData = useMemo(() => {
    if (!tree) return [];
    return [
      { id: "root-substations", label: "Substations", kind: "Group", attrs: {}, children: tree.substations },
      { id: "root-ieds", label: "IEDs", kind: "Group", attrs: {}, children: tree.ieds },
    ];
  }, [tree]);

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", display: "flex", height: "100vh" }}>
      <div style={{ width: 220, borderRight: "1px solid #ddd", padding: 12, overflowY: "auto" }}>
        <h2 style={{ fontSize: 16 }}>SCL Explorer</h2>
        <ul style={{ listStyle: "none", padding: 0 }}>
          {files.map((f) => (
            <li
              key={f}
              onClick={() => openFile(f)}
              style={{
                padding: "6px 4px",
                cursor: "pointer",
                background: f === selectedFile ? "#eef" : "transparent",
                fontSize: 13,
                wordBreak: "break-all",
              }}
            >
              {f}
            </li>
          ))}
        </ul>
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <div style={{ borderBottom: "1px solid #ddd", padding: "8px 16px", display: "flex", gap: 16 }}>
          <button onClick={() => setTab("tree")} disabled={tab === "tree"}>
            Tree
          </button>
          <button onClick={() => setTab("validation")} disabled={tab === "validation"}>
            Validation {report ? `(${report.error_count}E / ${report.warning_count}W)` : ""}
          </button>
          {loading && <span>Loading...</span>}
          {error && <span style={{ color: "crimson" }}>{error}</span>}
        </div>

        {!selectedFile && (
          <p style={{ padding: 16, color: "#888" }}>Select a file on the left to open it.</p>
        )}

        {selectedFile && tab === "tree" && (
          <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <TreeView data={treeData} onSelect={setSelectedNode} width="100%" height={window.innerHeight - 50} />
            </div>
            <div style={{ width: 320, borderLeft: "1px solid #ddd", padding: 12, overflowY: "auto" }}>
              <NodeDetails node={selectedNode} />
            </div>
          </div>
        )}

        {selectedFile && tab === "validation" && (
          <div style={{ padding: 16, overflowY: "auto" }}>
            <ValidationPanel report={report} />
          </div>
        )}
      </div>
    </div>
  );
}
