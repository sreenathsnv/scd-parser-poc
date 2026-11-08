from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import store
from ..graph import loader
from ..graph.neo4j_client import run_query

router = APIRouter(tags=["graph"])


@router.post("/files/{filename}/graph-load")
def graph_load(filename: str) -> dict:
    doc = store.get(filename)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"{filename} has not been parsed yet; POST /files/{filename}/parse first")
    return loader.ingest(doc)


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
