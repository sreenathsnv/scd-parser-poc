from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import config, store
from ..graph import loader
from ..graph.neo4j_client import run_query

router = APIRouter(tags=["graph"])

CONTROL_LABELS = ["GSEControl", "SampledValueControl", "ReportControl"]


@router.post("/files/{filename:path}/graph-load")
def graph_load(filename: str) -> dict:
    doc = store.get(filename)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"{filename} has not been parsed yet; POST /files/{filename}/parse first")
    return loader.ingest(doc)


@router.get("/files/{filename:path}/graph-view")
def graph_view(filename: str) -> dict:
    """Collapsed IED/control-block/dataset/SubNetwork overview graph for one
    file, in Cytoscape.js elements shape. Not the full DO/DA instance tree
    (the tree view already covers that) -- this is the dataflow layer:
    which IEDs publish/subscribe to which control blocks over which
    SubNetwork, and which datasets each control block carries.
    """
    sp = config.resolve_path(filename)
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(key: str, label: str, kind: str, **extra):
        nodes[key] = {"data": {"id": key, "label": label, "kind": kind, **extra}}

    def add_edge(source: str, target: str, kind: str):
        edges.append({"data": {"id": f"{source}->{kind}->{target}", "source": source, "target": target, "kind": kind}})

    for row in run_query("MATCH (ied:IED {sourcePath: $sp}) RETURN ied.key AS key, ied.name AS name", sp=sp):
        add_node(row["key"], row["name"], "IED")

    for row in run_query("MATCH (sn:SubNetwork {sourcePath: $sp}) RETURN sn.key AS key, sn.name AS name", sp=sp):
        add_node(row["key"], row["name"], "SubNetwork")

    for row in run_query(
        """
        MATCH (ied:IED {sourcePath: $sp})-[:CONNECTED_VIA]->(:ConnectedAP)-[:ON]->(sn:SubNetwork)
        RETURN DISTINCT ied.key AS iedKey, sn.key AS snKey
        """,
        sp=sp,
    ):
        add_edge(row["iedKey"], row["snKey"], "ON")

    for row in run_query(
        """
        MATCH (ied:IED {sourcePath: $sp})-[:CONTAINS*]->(cb)
        WHERE any(l IN labels(cb) WHERE l IN $controlLabels)
        RETURN DISTINCT ied.key AS iedKey, cb.key AS cbKey, cb.name AS cbName, labels(cb) AS cbLabels
        """,
        sp=sp,
        controlLabels=CONTROL_LABELS,
    ):
        kind = next(l for l in row["cbLabels"] if l in CONTROL_LABELS)
        add_node(row["cbKey"], row["cbName"], kind)
        add_edge(row["iedKey"], row["cbKey"], "PUBLISHES")

    for row in run_query(
        """
        MATCH (cb {sourcePath: $sp})-[:PUBLISHES]->(ds:DataSet)
        WHERE any(l IN labels(cb) WHERE l IN $controlLabels)
        RETURN DISTINCT cb.key AS cbKey, ds.key AS dsKey, ds.name AS dsName
        """,
        sp=sp,
        controlLabels=CONTROL_LABELS,
    ):
        add_node(row["dsKey"], row["dsName"], "DataSet")
        add_edge(row["cbKey"], row["dsKey"], "PUBLISHES")

    for row in run_query(
        """
        MATCH (subIed:IED {sourcePath: $sp})-[:CONTAINS*]->(:LogicalNode)-[:SUBSCRIBES_TO]->(cb)
        WHERE any(l IN labels(cb) WHERE l IN $controlLabels)
        RETURN DISTINCT subIed.key AS iedKey, cb.key AS cbKey
        """,
        sp=sp,
        controlLabels=CONTROL_LABELS,
    ):
        if row["cbKey"] in nodes:
            add_edge(row["iedKey"], row["cbKey"], "SUBSCRIBES_TO")

    return {"nodes": list(nodes.values()), "edges": edges}


@router.get("/graph/subnetworks/{name}/ieds")
def ieds_on_subnetwork(name: str) -> list[dict]:
    """IEDs on SubNetwork Y and their IPs."""
    return run_query(
        """
        MATCH (sn:SubNetwork {name: $name})-[:CONTAINS]->(cap:ConnectedAP)
        RETURN cap.iedName AS iedName, cap.ipAddr AS ip, cap.ipSubnet AS subnet, cap.ipGateway AS gateway
        """,
        name=name,
    )


@router.get("/graph/ieds/{name}/goose-subscribers")
def goose_subscribers(name: str) -> list[dict]:
    """Which IEDs subscribe to GOOSE published by IED X."""
    return run_query(
        """
        MATCH (pubIed:IED {name: $name})-[:CONTAINS*]->(gc:GSEControl)
        MATCH (subLn:LogicalNode)-[:SUBSCRIBES_TO]->(gc)
        MATCH (subIed:IED)-[:CONTAINS*]->(subLn)
        RETURN DISTINCT subIed.name AS subscriberIed
        """,
        name=name,
    )


@router.get("/graph/empty-control-blocks")
def empty_control_blocks() -> list[dict]:
    """Control blocks with no datSet, or whose datSet has zero FCDA members."""
    return run_query(
        """
        MATCH (cb)
        WHERE any(l IN labels(cb) WHERE l IN ['GSEControl', 'SampledValueControl', 'ReportControl'])
        OPTIONAL MATCH (cb)-[:PUBLISHES]->(ds:DataSet)
        OPTIONAL MATCH (ds)-[:HAS_MEMBER]->(fcda:FCDA)
        WITH cb, ds, count(fcda) AS memberCount
        WHERE ds IS NULL OR memberCount = 0
        RETURN labels(cb) AS kind, cb.name AS name, cb.sourcePath AS sourcePath, ds.name AS dataset
        """
    )
