from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException

from .. import config, store
from ..validation import custom_rules

router = APIRouter(prefix="/files", tags=["validation"])


@router.get("/{filename:path}/validate")
async def validate_file(filename: str) -> dict:
    doc = store.get(filename)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"{filename} has not been parsed yet; POST /files/{filename}/parse first")

    custom_report = custom_rules.run_all(doc)
    result = custom_report.to_dict()
    result["sidecar"] = await _call_sidecar(filename, doc.raw_bytes)
    return result


async def _call_sidecar(filename: str, raw_bytes: bytes) -> dict:
    url = f"{config.VALIDATION_SIDECAR_URL}/validate"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, content=raw_bytes, params={"filename": filename})
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as exc:
        return {
            "status": "unavailable",
            "message": f"validation-sidecar not reachable ({exc}); XSD/OCL findings skipped, custom-rule findings above are unaffected",
            "findings": [],
        }
