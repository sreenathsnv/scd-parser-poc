"""POST /files/import: the uploaded file becomes the active working document,
kept under its own imported/ subfolder, and every other endpoint accepts the
resulting slash-containing name correctly ({filename:path}, not {filename}).
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app import config
from app.main import app

RESOURCES_DIR = Path(__file__).resolve().parents[3] / "Resources"


def test_import_then_tree_and_validate(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "FILES_DIR", tmp_path)
    client = TestClient(app)

    content = (RESOURCES_DIR / "project.scd").read_bytes()
    resp = client.post("/files/import", files={"file": ("my_upload.scd", content, "application/octet-stream")})
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "imported/my_upload.scd"
    assert data["iedCount"] == 1
    assert (tmp_path / "imported" / "my_upload.scd").exists()

    listed = client.get("/files").json()
    assert "imported/my_upload.scd" in listed["files"]

    tree_resp = client.get("/files/imported/my_upload.scd/tree")
    assert tree_resp.status_code == 200
    assert len(tree_resp.json()["ieds"]) == 1

    validate_resp = client.get("/files/imported/my_upload.scd/validate")
    assert validate_resp.status_code == 200


def test_import_rejects_unsupported_extension(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "FILES_DIR", tmp_path)
    client = TestClient(app)
    resp = client.post("/files/import", files={"file": ("not-scl.txt", b"hello", "text/plain")})
    assert resp.status_code == 400


def test_import_name_collision_gets_disambiguated(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "FILES_DIR", tmp_path)
    client = TestClient(app)
    content = (RESOURCES_DIR / "project.scd").read_bytes()

    first = client.post("/files/import", files={"file": ("dup.scd", content, "application/octet-stream")}).json()
    second = client.post("/files/import", files={"file": ("dup.scd", content, "application/octet-stream")}).json()

    assert first["filename"] == "imported/dup.scd"
    assert second["filename"] == "imported/dup-2.scd"
    assert (tmp_path / "imported" / "dup.scd").exists()
    assert (tmp_path / "imported" / "dup-2.scd").exists()
