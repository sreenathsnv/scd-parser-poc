"""Validation snapshots pinned to known defects: MAYZAN's duplicate IPs, DTech26's missing Substation."""
from __future__ import annotations

from pathlib import Path

from app.scl import parser
from app.validation import custom_rules

RESOURCES_DIR = Path(__file__).resolve().parents[3] / "Resources"


def _rules_fired(report, rule: str) -> list:
    return [f for f in report.findings if f.rule == rule]


def test_mayzan_duplicate_ip_defect_surfaces():
    path = RESOURCES_DIR / "MAYZAN_400_132_11_KV_SS_PCM600_FILES[1] (1).scd"
    doc = parser.parse_file(str(path))
    report = custom_rules.run_all(doc)

    dup_ip = _rules_fired(report, "duplicate-ip")
    errors = [f for f in dup_ip if f.severity.value == "error"]
    assert len(errors) == 1
    assert errors[0].details["ip"] == "10.1.150.3"
    assert set(errors[0].details["ieds"]) == {"IED_CD1RL670", "IED_CD1RQ650", "IED_CD1RT670"}


def test_dtech26_missing_substation_defect_surfaces():
    path = RESOURCES_DIR / "DTech26_vPAC 4 (2).scd"
    doc = parser.parse_file(str(path))
    assert len(doc.substations) == 0

    report = custom_rules.run_all(doc)
    missing_sub = _rules_fired(report, "missing-substation")
    assert len(missing_sub) == 1
    assert missing_sub[0].severity.value == "error"


def test_project_scd_and_icd_are_clean():
    for name in ["project.scd", "IEC61850.icd"]:
        doc = parser.parse_file(str(RESOURCES_DIR / name))
        report = custom_rules.run_all(doc)
        assert report.error_count == 0, f"{name}: unexpected error findings {report.findings}"
