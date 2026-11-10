"""Writes a (possibly edited) SclDocument back to SCL XML.

Unmodified documents are written back as the exact original bytes (lxml
would otherwise normalize line endings/declaration quoting, breaking a
byte-diff round trip). Edited documents serialize the mutated lxml tree,
then re-match line endings to the source file's CRLF/LF convention.
"""
from __future__ import annotations

from lxml import etree

from . import model as m


def serialize(doc: m.SclDocument) -> bytes:
    if not doc.dirty:
        return doc.raw_bytes

    tree: etree._ElementTree = doc._lxml_tree
    docinfo_encoding = "UTF-8"
    body = etree.tostring(tree, xml_declaration=False, encoding=docinfo_encoding)

    decl = f'<?xml version="1.0" encoding="{docinfo_encoding}"?>'.encode("ascii")
    out = decl + b"\n" + body if not body.startswith(b"\n") else decl + body

    if doc.uses_crlf:
        out = out.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")

    return out


def write_file(doc: m.SclDocument, path: str) -> None:
    data = serialize(doc)
    with open(path, "wb") as f:
        f.write(data)
