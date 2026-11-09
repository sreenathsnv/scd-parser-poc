import React, { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

const KIND_STYLE = {
  IED: { shape: "round-rectangle", color: "#2980b9" },
  SubNetwork: { shape: "diamond", color: "#555" },
  GSEControl: { shape: "ellipse", color: "#16a085" },
  SampledValueControl: { shape: "ellipse", color: "#8e44ad" },
  ReportControl: { shape: "ellipse", color: "#d68910" },
  DataSet: { shape: "rectangle", color: "#c0392b" },
};

const EDGE_COLOR = { PUBLISHES: "#aaa", SUBSCRIBES_TO: "#2980b9", ON: "#999" };

export default function GraphView({ elements, onSelect }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const cy = cytoscape({
      container: containerRef.current,
      elements: [...elements.nodes, ...elements.edges],
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "font-size": 9,
            width: 28,
            height: 28,
            "background-color": (el) => KIND_STYLE[el.data("kind")]?.color || "#888",
            shape: (el) => KIND_STYLE[el.data("kind")]?.shape || "ellipse",
            color: "#222",
            "text-valign": "bottom",
            "text-margin-y": 4,
            "text-wrap": "ellipsis",
            "text-max-width": 80,
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": (el) => EDGE_COLOR[el.data("kind")] || "#ccc",
            "target-arrow-color": (el) => EDGE_COLOR[el.data("kind")] || "#ccc",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            opacity: 0.8,
          },
        },
        {
          selector: "node:selected",
          style: { "border-width": 3, "border-color": "#222" },
        },
      ],
      layout: { name: "cose", animate: false, nodeRepulsion: 8000, idealEdgeLength: 80 },
    });

    cy.on("select", "node", (evt) => onSelect(evt.target.data()));
    cyRef.current = cy;

    cy.resize();
    cy.fit(undefined, 20);
    const onResize = () => {
      cy.resize();
      cy.fit(undefined, 20);
    };
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      cy.destroy();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [elements]);

  return <div ref={containerRef} style={{ flex: 1, minWidth: 0, minHeight: 0, background: "#fafafa" }} />;
}
