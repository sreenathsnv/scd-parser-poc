from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import config, store
from ..scl import parser, projection, serializer

router = APIRouter(prefix="/files", tags=["files"])


def _resolve_path(filename: str) -> str:
    path = config.FILES_DIR / filename
    if ".." in filename or path.is_absolute() and not str(path).startswith(str(config.FILES_DIR)):
        raise HTTPException(status_code=400, detail="invalid filename")
    return str(path)


@router.get("")
def list_files() -> dict:
    if not config.FILES_DIR.exists():
        return {"filesDir": str(config.FILES_DIR), "files": []}
    names = sorted(
        p.name for p in config.FILES_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in (".scd", ".icd", ".cid", ".ssd", ".sed")
    )
    return {"filesDir": str(config.FILES_DIR), "files": names}


@router.post("/{filename}/parse")
def parse_file(filename: str) -> dict:
    path = _resolve_path(filename)
    try:
        doc = parser.parse_file(path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{filename} not found under {config.FILES_DIR}")
    except parser.ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    store.put(filename, doc)
    return projection.to_summary(doc)


@router.get("/{filename}/summary")
def get_summary(filename: str) -> dict:
    doc = store.get(filename)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"{filename} has not been parsed yet; POST /files/{filename}/parse first")
    return projection.to_summary(doc)


@router.post("/{filename}/save-as-copy")
def save_as_copy(filename: str, new_filename: str) -> dict:
    doc = store.get(filename)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"{filename} has not been parsed yet")
    new_path = _resolve_path(new_filename)
    serializer.write_file(doc, new_path)
    return {"written": new_filename, "dirty": doc.dirty}


@router.post("/{filename}/save-overwrite")
def save_overwrite(filename: str, confirm: bool = False) -> dict:
    """Overwrites the original file; `confirm` is a backstop, not a substitute for the UI's own warning."""
    if not confirm:
        raise HTTPException(status_code=400, detail="overwrite requires confirm=true")
    doc = store.get(filename)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"{filename} has not been parsed yet")
    path = _resolve_path(filename)
    serializer.write_file(doc, path)
    return {"overwritten": filename, "dirty": doc.dirty}
