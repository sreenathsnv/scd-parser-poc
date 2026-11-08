"""Thin wrapper around the official neo4j Python driver."""
from __future__ import annotations

import os

from neo4j import Driver, GraphDatabase

_driver: Driver | None = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "changeme")
        _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def run_query(cypher: str, **params) -> list[dict]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher, **params)
        return [record.data() for record in result]


def ensure_constraints() -> None:
    from .schema import constraint_statements, index_statements

    driver = get_driver()
    with driver.session() as session:
        for stmt in constraint_statements():
            session.run(stmt)
        for stmt in index_statements():
            session.run(stmt)
