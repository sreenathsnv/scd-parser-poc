import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import TreeView from "./components/TreeView";
import NodeDetails from "./components/NodeDetails";
import ValidationPanel from "./components/ValidationPanel";
import GraphView from "./components/GraphView";
import { SaveAsCopyDialog, OverwriteConfirmDialog } from "./components/SaveDialog";

export default function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [tree, setTree] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [report, setReport] = useState(null);
  const [dirty, setDirty] = useState(false);
  const [graphElements, setGraphElements] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [tab, setTab] = useState("tree");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saveDialog, setSaveDialog] = useState(null); // "copy" | "overwrite" | null
  const [statusMessage, setStatusMessage] = useState(null);

  function refreshFileList() {
    api.listFiles().then((d) => setFiles(d.files)).catch((e) => setError(e.message));
  }

  useEffect(refreshFileList, []);

  async function openFile(name) {
    setError(null);
    setSaveError(null);
    setStatusMessage(null);
    setLoading(true);
    setSelectedFile(name);
    setSelectedNode(null);
    setGraphElements(null);
    try {
      const summary = await api.parseFile(name);
      setDirty(summary.dirty);
      const [t, v] = await Promise.all([api.getTree(name), api.validate(name)]);
      setTree(t);
      setReport(v);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function refreshTreeAndValidation() {
    const [t, v] = await Promise.all([api.getTree(selectedFile), api.validate(selectedFile)]);
    setTree(t);
    setReport(v);
  }

  async function handleSaveDai(node, value) {
    setSaving(true);
    setSaveError(null);
    try {
      const result = await api.editDai(selectedFile, {
        iedName: node.attrs.iedName,
        ldInst: node.attrs.ldInst,
        lnPrefix: node.attrs.lnPrefix,
        lnClass: node.attrs.lnClass,
        lnInst: node.attrs.lnInst,
        doiPath: node.attrs.doiPath,
        daiName: node.attrs.daiName,
        value,
      });
      setDirty(result.dirty);
      await refreshTreeAndValidation();
      setSelectedNode({ ...node, attrs: { ...node.attrs, val: value } });
    } catch (e) {
      setSaveError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function confirmSaveAsCopy(newName) {
    setSaveDialog(null);
    try {
      await api.saveAsCopy(selectedFile, newName);
      refreshFileList();
      setStatusMessage(`Saved as ${newName}. The original file was not modified.`);
    } catch (e) {
      setError(e.message);
    }
  }

  async function confirmSaveOverwrite() {
    setSaveDialog(null);
    try {
      const result = await api.saveOverwrite(selectedFile);
      setDirty(result.dirty);
      setStatusMessage(`${selectedFile} overwritten.`);
    } catch (e) {
      setError(e.message);
    }
  }

  async function openGraphTab() {
    setTab("graph");
    if (graphElements || !selectedFile) return;
    setGraphLoading(true);
    setError(null);
    try {
      await api.graphLoad(selectedFile);
      const g = await api.getGraphView(selectedFile);
      setGraphElements(g);
    } catch (e) {
      setError(e.message);
    } finally {
      setGraphLoading(false);
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
        <div style={{ borderBottom: "1px solid #ddd", padding: "8px 16px", display: "flex", gap: 16, alignItems: "center" }}>
          <button onClick={() => setTab("tree")} disabled={tab === "tree"}>
            Tree
          </button>
          <button onClick={openGraphTab} disabled={tab === "graph"}>
            Graph
          </button>
          <button onClick={() => setTab("validation")} disabled={tab === "validation"}>
            Validation {report ? `(${report.error_count}E / ${report.warning_count}W)` : ""}
          </button>

          {selectedFile && (
            <span style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
              {dirty && <span style={{ color: "#d68910", fontSize: 12 }}>unsaved changes</span>}
              <button onClick={() => setSaveDialog("copy")}>Save as copy</button>
              <button onClick={() => setSaveDialog("overwrite")} disabled={!dirty}>
                Save (overwrite)
              </button>
            </span>
          )}

          {(loading || graphLoading) && <span>Loading...</span>}
          {error && <span style={{ color: "crimson" }}>{error}</span>}
          {statusMessage && <span style={{ color: "#2e7d32" }}>{statusMessage}</span>}
        </div>

        {saveDialog === "copy" && (
          <SaveAsCopyDialog
            suggestedName={selectedFile.replace(/(\.[a-zA-Z]+)$/, "-edited$1")}
            onConfirm={confirmSaveAsCopy}
            onCancel={() => setSaveDialog(null)}
          />
        )}
        {saveDialog === "overwrite" && (
          <OverwriteConfirmDialog
            filename={selectedFile}
            onConfirm={confirmSaveOverwrite}
            onCancel={() => setSaveDialog(null)}
          />
        )}

        {!selectedFile && (
          <p style={{ padding: 16, color: "#888" }}>Select a file on the left to open it.</p>
        )}

        {selectedFile && tab === "tree" && (
          <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <TreeView data={treeData} onSelect={setSelectedNode} width="100%" height={window.innerHeight - 50} />
            </div>
            <div style={{ width: 320, borderLeft: "1px solid #ddd", padding: 12, overflowY: "auto" }}>
              <NodeDetails node={selectedNode} onSaveDai={handleSaveDai} saving={saving} saveError={saveError} />
            </div>
          </div>
        )}

        {selectedFile && tab === "graph" && (
          <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
            {graphElements ? (
              <GraphView
                elements={graphElements}
                onSelect={(d) => setSelectedNode({ label: d.label, kind: d.kind, attrs: { id: d.id } })}
              />
            ) : (
              <p style={{ flex: 1, padding: 16, color: "#888" }}>{graphLoading ? "Loading graph..." : "No graph data."}</p>
            )}
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
