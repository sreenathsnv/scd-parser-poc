"""Mutates a parsed SclDocument's DAI values, in both the lxml tree (for the
serializer) and the typed model (for live re-validation/re-projection),
then marks the document dirty.
"""
from __future__ import annotations

from lxml import etree

from . import model as m
from .parser import _attr, _child, _children


class EditError(Exception):
    pass


def _find_ied_element(root: etree._Element, ied_name: str) -> etree._Element:
    for ied_el in _children(root, "IED"):
        if _attr(ied_el, "name") == ied_name:
            return ied_el
    raise EditError(f"IED '{ied_name}' not found")


def _find_ldevice_element(ied_el: etree._Element, ld_inst: str) -> etree._Element:
    for ap_el in _children(ied_el, "AccessPoint"):
        server_el = _child(ap_el, "Server")
        if server_el is None:
            continue
        for ld_el in _children(server_el, "LDevice"):
            if _attr(ld_el, "inst") == ld_inst:
                return ld_el
    raise EditError(f"LDevice '{ld_inst}' not found on IED")


def _find_ln_element(ld_el: etree._Element, prefix: str, ln_class: str, inst: str) -> etree._Element:
    candidates = _children(ld_el, "LN0") + _children(ld_el, "LN")
    for ln_el in candidates:
        if (
            _attr(ln_el, "lnClass") == ln_class
            and _attr(ln_el, "inst", "") == inst
            and (_attr(ln_el, "prefix") or "") == prefix
        ):
            return ln_el
    raise EditError(f"LN '{prefix}{ln_class}{inst}' not found on LDevice")


def _find_doi_chain_element(ln_el: etree._Element, doi_path: list[str]) -> etree._Element:
    if not doi_path:
        raise EditError("empty doiPath")
    current = None
    for doi_el in _children(ln_el, "DOI"):
        if _attr(doi_el, "name") == doi_path[0]:
            current = doi_el
            break
    if current is None:
        raise EditError(f"DOI '{doi_path[0]}' not found on LN")
    for name in doi_path[1:]:
        found = None
        for sdi_el in _children(current, "SDI"):
            if _attr(sdi_el, "name") == name:
                found = sdi_el
                break
        if found is None:
            raise EditError(f"SDI '{name}' not found")
        current = found
    return current


def _find_dai_element(parent_el: etree._Element, dai_name: str) -> etree._Element:
    for dai_el in _children(parent_el, "DAI"):
        if _attr(dai_el, "name") == dai_name:
            return dai_el
    raise EditError(f"DAI '{dai_name}' not found")


def _set_val_text(dai_el: etree._Element, value: str) -> None:
    val_el = _child(dai_el, "Val")
    if val_el is None:
        ns = dai_el.tag[: dai_el.tag.index("}") + 1] if dai_el.tag.startswith("{") else ""
        val_el = etree.SubElement(dai_el, f"{ns}Val")
    val_el.text = value


def _find_doi_chain_model(ln: m.LogicalNode, doi_path: list[str]) -> m.DOI | m.SDI:
    current: m.DOI | m.SDI | None = None
    for doi in ln.doi:
        if doi.name == doi_path[0]:
            current = doi
            break
    if current is None:
        raise EditError(f"DOI '{doi_path[0]}' not found in model")
    for name in doi_path[1:]:
        found = None
        for sdi in current.sdi_children:
            if sdi.name == name:
                found = sdi
                break
        if found is None:
            raise EditError(f"SDI '{name}' not found in model")
        current = found
    return current


def set_dai_value(
    doc: m.SclDocument,
    ied_name: str,
    ld_inst: str,
    ln_prefix: str,
    ln_class: str,
    ln_inst: str,
    doi_path: list[str],
    dai_name: str,
    value: str,
) -> None:
    root: etree._Element = doc._lxml_tree.getroot()
    ied_el = _find_ied_element(root, ied_name)
    ld_el = _find_ldevice_element(ied_el, ld_inst)
    ln_el = _find_ln_element(ld_el, ln_prefix, ln_class, ln_inst)
    container_el = _find_doi_chain_element(ln_el, doi_path)
    dai_el = _find_dai_element(container_el, dai_name)
    _set_val_text(dai_el, value)

    ied = doc.find_ied(ied_name)
    if ied is None:
        raise EditError(f"IED '{ied_name}' not found in model")
    ld = next((l for l in ied.all_ldevices if l.inst == ld_inst), None)
    if ld is None:
        raise EditError(f"LDevice '{ld_inst}' not found in model")
    ln = next(
        (n for n in ld.all_lns if n.ln_class == ln_class and n.inst == ln_inst and (n.prefix or "") == ln_prefix),
        None,
    )
    if ln is None:
        raise EditError("LN not found in model")
    container = _find_doi_chain_model(ln, doi_path)
    dai = next((d for d in container.dai_children if d.name == dai_name), None)
    if dai is None:
        raise EditError(f"DAI '{dai_name}' not found in model")
    dai.values = [value]

    doc.dirty = True
    doc.unsaved = True
