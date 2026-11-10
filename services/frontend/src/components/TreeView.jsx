import React from "react";
import { Tree } from "react-arborist";

const KIND_COLORS = {
  Substation: "#8e44ad",
  VoltageLevel: "#8e44ad",
  Bay: "#8e44ad",
  ConductingEquipment: "#8e44ad",
  LNodeRef: "#8e44ad",
  IED: "#2980b9",
  AccessPoint: "#2980b9",
  Server: "#2980b9",
  LDevice: "#2980b9",
  LogicalNode: "#16a085",
  DataObject: "#d35400",
  DataAttribute: "#c0392b",
  Group: "#333",
};

function Node({ node, style, dragHandle }) {
  const kind = node.data.kind;
  const color = KIND_COLORS[kind] || "#333";
  return (
    <div
      style={{ ...style, display: "flex", alignItems: "center", cursor: "pointer", fontSize: 13 }}
      ref={dragHandle}
      onClick={() => node.isInternal && node.toggle()}
    >
      <span style={{ marginRight: 6 }}>{node.isLeaf ? "" : node.isOpen ? "▾" : "▸"}</span>
      <span style={{ color, fontWeight: 600, marginRight: 6 }}>{kind}</span>
      <span>{node.data.label}</span>
    </div>
  );
}

export default function TreeView({ data, onSelect, width, height }) {
  return (
    <Tree
      data={data}
      width={width}
      height={height}
      rowHeight={24}
      indent={16}
      openByDefault={false}
      onSelect={(nodes) => nodes[0] && onSelect(nodes[0].data)}
    >
      {Node}
    </Tree>
  );
}
