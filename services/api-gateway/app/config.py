from __future__ import annotations

import os
from pathlib import Path

# bind-mounted host directory holding the real SCD/ICD/CID files
FILES_DIR = Path(os.environ.get("SCD_FILES_DIR", "/data/scl-files"))

VALIDATION_SIDECAR_URL = os.environ.get("VALIDATION_SIDECAR_URL", "http://validation-sidecar:8080")
MODEL_GENERATOR_URL = os.environ.get("MODEL_GENERATOR_URL", "http://model-generator:8080")


def resolve_path(filename: str) -> str:
    return str(FILES_DIR / filename)
