"""Edit a DAI value, save as copy, reopen the copy and confirm the edit
persisted and the original file is untouched -- the Phase 1 acceptance
check from the technical plan.
"""
from __future__ import annotations

from pathlib import Path

from app.scl import editor, parser, serializer

RESOURCES_DIR = Path(__file__).resolve().parents[3] / "Resources"


def test_edit_save_as_copy_round_trip(tmp_path):
    original_path = RESOURCES_DIR / "IEC61850.icd"
    original_bytes = original_path.read_bytes()

    doc = parser.parse_file(str(original_path))
    ied = doc.ieds[0]
    ld = ied.all_ldevices[0]
    ln0 = ld.ln0

    editor.set_dai_value(doc, ied.name, ld.inst, ln0.prefix or "", ln0.ln_class, ln0.inst, ["NamPlt"], "vendor", "TriviumTest")
    assert doc.dirty is True

    copy_path = tmp_path / "edited_copy.icd"
    serializer.write_file(doc, str(copy_path))

    assert original_path.read_bytes() == original_bytes, "original file must stay untouched"

    reopened = parser.parse_file(str(copy_path))
    reopened_doi = next(d for d in reopened.ieds[0].all_ldevices[0].ln0.doi if d.name == "NamPlt")
    reopened_dai = next(d for d in reopened_doi.dai_children if d.name == "vendor")
    assert reopened_dai.values == ["TriviumTest"]


def test_overwrite_then_save_as_copy_keeps_edit(tmp_path):
    """doc.dirty (serializer's permanent flag) must never be reset by a save,
    only doc.unsaved (the UI's flag) -- otherwise a save-as-copy performed
    after an overwrite would wrongly fall back to serializing raw_bytes
    (the pre-edit content) instead of the edited lxml tree.
    """
    original_path = RESOURCES_DIR / "IEC61850.icd"
    overwrite_path = tmp_path / "overwritten.icd"
    overwrite_path.write_bytes(original_path.read_bytes())

    doc = parser.parse_file(str(overwrite_path))
    ied = doc.ieds[0]
    ld = ied.all_ldevices[0]
    ln0 = ld.ln0
    editor.set_dai_value(doc, ied.name, ld.inst, ln0.prefix or "", ln0.ln_class, ln0.inst, ["NamPlt"], "vendor", "TriviumTest")

    serializer.write_file(doc, str(overwrite_path))
    doc.unsaved = False  # mirrors what the save-overwrite endpoint does

    copy_path = tmp_path / "copy_after_overwrite.icd"
    serializer.write_file(doc, str(copy_path))

    reopened = parser.parse_file(str(copy_path))
    dai = next(
        d for d in reopened.ieds[0].all_ldevices[0].ln0.doi if d.name == "NamPlt"
    ).dai_children
    assert next(d for d in dai if d.name == "vendor").values == ["TriviumTest"]


def test_edit_unknown_dai_raises():
    doc = parser.parse_file(str(RESOURCES_DIR / "IEC61850.icd"))
    ied = doc.ieds[0]
    ld = ied.all_ldevices[0]
    ln0 = ld.ln0
    try:
        editor.set_dai_value(doc, ied.name, ld.inst, ln0.prefix or "", ln0.ln_class, ln0.inst, ["NamPlt"], "doesNotExist", "x")
        assert False, "expected EditError"
    except editor.EditError:
        pass
