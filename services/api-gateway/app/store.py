"""In-process cache of parsed documents, keyed by filename."""
from __future__ import annotations

from .scl import model as m

_documents: dict[str, m.SclDocument] = {}


def put(filename: str, doc: m.SclDocument) -> None:
    _documents[filename] = doc


def get(filename: str) -> m.SclDocument | None:
    return _documents.get(filename)


def drop(filename: str) -> None:
    _documents.pop(filename, None)
