from __future__ import annotations

from pathlib import Path

import pytest

RESOURCES_DIR = Path(__file__).resolve().parents[3] / "Resources"

RESOURCE_FILES = [
    RESOURCES_DIR / "project.scd",
    RESOURCES_DIR / "IEC61850.icd",
    RESOURCES_DIR / "MAYZAN_400_132_11_KV_SS_PCM600_FILES[1] (1).scd",
    RESOURCES_DIR / "DTech26_vPAC 4 (2).scd",
]


@pytest.fixture(params=RESOURCE_FILES, ids=[p.name for p in RESOURCE_FILES])
def resource_file(request) -> Path:
    return request.param
