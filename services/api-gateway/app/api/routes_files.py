from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from .. import config, store
from ..scl import editor, parser, projection, serializer

router = APIRouter(prefix="/files", tags=["files"])


class EditDaiRequest(BaseModel):
    iedName: str
    ldInst: str
    lnPrefix: str = ""
    lnClass: str
    lnInst: str = ""
    doiPath: list[str]
    daiName: str
    value: str


def _resolve_path(filename: str) -> str:
    path = config.FILES_DIR / filename
    if ".." in filename or path.is_absolute() and not str(path).startswith(str(config.FILES_DIR)):
        raise HTTPException(status_code=400, detail="invalid filename")
    return config.resolve_path(filename)


def _is_scl_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in config.SCL_EXTENSIONS


@router.get("")
def list_files() -> dict:
    if not config.FILES_DIR.exists():
        return {"filesDir": str(config.FILES_DIR), "files": []}
    names = sorted(p.name for p in config.FILES_DIR.iterdir() if _is_scl_file(p))
    imports_dir = config.imports_dir()
    names += sorted(f"{config.IMPORTS_SUBDIR}/{p.name}" for p in imports_dir.iterdir() if _is_scl_file(p))
    return {"filesDir": str(config.FILES_DIR), "files": names}


def _unique_import_name(directory: Path, original_name: str) -> str:
    stem, suffix = Path(original_name).stem, Path(original_name).suffix
    candidate = original_name
    i = 1
    while (directory / candidate).exists():
        i += 1
        candidate = f"{stem}-{i}{suffix}"
    return candidate


@router.post("/import")
async def import_file(file: UploadFile = File(...)) -> dict:
    original_name = Path(file.filename or "upload").name  # strip any path components
    if Path(original_name).suffix.lower() not in config.SCL_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"unsupported file type; expected one of {config.SCL_EXTENSIONS}")

    directory = config.imports_dir()
    saved_name = _unique_import_name(directory, original_name)
    data = await file.read()
    (directory / saved_name).write_bytes(data)

    relative_name = f"{config.IMPORTS_SUBDIR}/{saved_name}"
    try:
        doc = parser.parse_file(str(directory / saved_name))
    except parser.ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    store.put(relative_name, doc)
    return {"filename": relative_name, **projection.to_summary(doc)}


@router.post("/{filename:path}/parse")
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


@router.get("/{filename:path}/summary")
def get_summary(filename: str) -> dict:
    doc = store.get(filename)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"{filename} has not been parsed yet; POST /files/{filename}/parse first")
    return projection.to_summary(doc)


@router.get("/{filename:path}/tree")
def get_tree(filename: str) -> dict:
    doc = store.get(filename)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"{filename} has not been parsed yet; POST /files/{filename}/parse first")
    return projection.to_tree(doc)


@router.post("/{filename:path}/edit/dai")
def edit_dai(filename: str, body: EditDaiRequest) -> dict:
    doc = store.get(filename)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"{filename} has not been parsed yet")
    try:
        editor.set_dai_value(
            doc, body.iedName, body.ldInst, body.lnPrefix, body.lnClass, body.lnInst,
            body.doiPath, body.daiName, body.value,
        )
    except editor.EditError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"dirty": doc.unsaved}


@router.post("/{filename:path}/save-as-copy")
def save_as_copy(filename: str, new_filename: str) -> dict:
    doc = store.get(filename)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"{filename} has not been parsed yet")
    new_path = _resolve_path(new_filename)
    serializer.write_file(doc, new_path)
    return {"written": new_filename, "dirty": doc.unsaved}


@router.post("/{filename:path}/save-overwrite")
def save_overwrite(filename: str, confirm: bool = False) -> dict:
    """Overwrites the original file; `confirm` is a backstop, not a substitute for the UI's own warning."""
    if not confirm:
        raise HTTPException(status_code=400, detail="overwrite requires confirm=true")
    doc = store.get(filename)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"{filename} has not been parsed yet")
    path = _resolve_path(filename)
    serializer.write_file(doc, path)
    doc.unsaved = False
    return {"overwritten": filename, "dirty": doc.unsaved}
