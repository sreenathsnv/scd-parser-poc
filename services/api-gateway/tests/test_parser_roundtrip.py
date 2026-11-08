"""Parser/serializer round-trip: parse -> no-op save -> byte-diff."""
from __future__ import annotations

from app.scl import parser, serializer


def test_parses_without_crashing(resource_file):
    doc = parser.parse_file(str(resource_file))
    assert doc.ieds, f"{resource_file.name}: expected at least one IED"


def test_noop_save_is_byte_identical(resource_file):
    original = resource_file.read_bytes()
    doc = parser.parse_file(str(resource_file))
    assert doc.dirty is False

    out = serializer.serialize(doc)

    assert out == original, f"{resource_file.name}: no-op round trip is not byte-identical"
