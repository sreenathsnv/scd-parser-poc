"""Parses an SCD/ICD/CID file into the typed object model in model.py."""
from __future__ import annotations

from lxml import etree

from . import model as m

SCL_NS = "http://www.iec.ch/61850/2003/SCL"


def _local(tag: str) -> str:
    """Strip any {namespace} prefix lxml attaches to a tag name."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _children(elem: etree._Element, name: str) -> list[etree._Element]:
    return [c for c in elem if isinstance(c.tag, str) and _local(c.tag) == name]


def _child(elem: etree._Element, name: str) -> etree._Element | None:
    found = _children(elem, name)
    return found[0] if found else None


def _attr(elem: etree._Element, name: str, default=None):
    return elem.get(name, default)


class ParseError(Exception):
    pass


def parse_file(path: str) -> m.SclDocument:
    with open(path, "rb") as f:
        raw = f.read()
    return parse_bytes(raw, source_path=path)


def parse_bytes(raw: bytes, source_path: str = "<memory>") -> m.SclDocument:
    parser = etree.XMLParser(
        remove_blank_text=False,
        strip_cdata=False,
        resolve_entities=False,
        huge_tree=True,
    )
    try:
        root = etree.fromstring(raw, parser=parser)
    except etree.XMLSyntaxError as exc:
        raise ParseError(f"{source_path}: not well-formed XML: {exc}") from exc

    if _local(root.tag) != "SCL":
        raise ParseError(f"{source_path}: root element is <{_local(root.tag)}>, expected <SCL>")

    doc = m.SclDocument(
        source_path=source_path,
        scl_version=_attr(root, "version"),
        scl_revision=_attr(root, "revision"),
        header=None,
    )
    doc._lxml_tree = root
    doc.raw_bytes = raw  # used by the serializer's verbatim fast-path
    doc.uses_crlf = b"\r\n" in raw

    _collect_private(root, "SCL", doc.privates)

    header_el = _child(root, "Header")
    if header_el is not None:
        doc.header = m.Header(
            id=_attr(header_el, "id", ""),
            version=_attr(header_el, "version"),
            revision=_attr(header_el, "revision"),
            tool_id=_attr(header_el, "toolID"),
            name_structure=_attr(header_el, "nameStructure"),
        )

    for sub_el in _children(root, "Substation"):
        doc.substations.append(_parse_substation(sub_el))

    comm_el = _child(root, "Communication")
    if comm_el is not None:
        doc.communication = _parse_communication(comm_el)

    for ied_el in _children(root, "IED"):
        doc.ieds.append(_parse_ied(ied_el))

    dtt_el = _child(root, "DataTypeTemplates")
    if dtt_el is not None:
        doc.data_type_templates = _parse_data_type_templates(dtt_el)

    return doc


def _collect_private(elem: etree._Element, path: str, sink: list[m.PrivateBlob]) -> None:
    for child in _children(elem, "Private"):
        sink.append(m.PrivateBlob(type=_attr(child, "type", ""), source=child, parent_path=path))
    for child in elem:
        if isinstance(child.tag, str) and _local(child.tag) != "Private":
            _collect_private(child, f"{path}/{_local(child.tag)}", sink)


# ---------------------------------------------------------------------------
# Substation section
# ---------------------------------------------------------------------------

def _parse_substation(el: etree._Element) -> m.Substation:
    sub = m.Substation(name=_attr(el, "name", ""), desc=_attr(el, "desc"))
    for vl_el in _children(el, "VoltageLevel"):
        sub.voltage_levels.append(_parse_voltage_level(vl_el))
    return sub


def _parse_voltage_level(el: etree._Element) -> m.VoltageLevel:
    vl = m.VoltageLevel(
        name=_attr(el, "name", ""),
        desc=_attr(el, "desc"),
        nom_freq=_attr(el, "nomFreq"),
        num_phases=_attr(el, "numPhases"),
    )
    for bay_el in _children(el, "Bay"):
        vl.bays.append(_parse_bay(bay_el))
    return vl


def _parse_bay(el: etree._Element) -> m.Bay:
    bay = m.Bay(name=_attr(el, "name", ""), desc=_attr(el, "desc"))
    for ce_el in _children(el, "ConductingEquipment"):
        bay.conducting_equipment.append(_parse_conducting_equipment(ce_el))
    return bay


def _parse_conducting_equipment(el: etree._Element) -> m.ConductingEquipment:
    ce = m.ConductingEquipment(name=_attr(el, "name", ""), type=_attr(el, "type"), desc=_attr(el, "desc"))
    for lnode_el in _children(el, "LNode"):
        ce.lnodes.append(
            m.LNodeRef(
                iedName=_attr(lnode_el, "iedName"),
                ldInst=_attr(lnode_el, "ldInst"),
                prefix=_attr(lnode_el, "prefix"),
                lnClass=_attr(lnode_el, "lnClass"),
                lnInst=_attr(lnode_el, "lnInst"),
            )
        )
    return ce


# ---------------------------------------------------------------------------
# Communication section
# ---------------------------------------------------------------------------

def _parse_addresses(el: etree._Element) -> list[m.AddressPoint]:
    out = []
    addr_el = _child(el, "Address")
    if addr_el is None:
        return out
    for p_el in _children(addr_el, "P"):
        out.append(m.AddressPoint(type=_attr(p_el, "type", ""), value=(p_el.text or "").strip()))
    return out


def _parse_communication(el: etree._Element) -> m.Communication:
    comm = m.Communication()
    for sn_el in _children(el, "SubNetwork"):
        sn = m.SubNetwork(name=_attr(sn_el, "name", ""), type=_attr(sn_el, "type"), desc=_attr(sn_el, "desc"))
        for cap_el in _children(sn_el, "ConnectedAP"):
            cap = m.ConnectedAP(
                ied_name=_attr(cap_el, "iedName", ""),
                ap_name=_attr(cap_el, "apName", ""),
                addresses=_parse_addresses(cap_el),
            )
            for gse_el in _children(cap_el, "GSE"):
                cap.gse.append(
                    m.GSE(
                        ld_inst=_attr(gse_el, "ldInst"),
                        cb_name=_attr(gse_el, "cbName"),
                        addresses=_parse_addresses(gse_el),
                        min_time=(_child(gse_el, "MinTime").get("unit") if _child(gse_el, "MinTime") is not None else None),
                        max_time=(_child(gse_el, "MaxTime").get("unit") if _child(gse_el, "MaxTime") is not None else None),
                    )
                )
            for smv_el in _children(cap_el, "SMV"):
                cap.smv.append(
                    m.SMV(
                        ld_inst=_attr(smv_el, "ldInst"),
                        cb_name=_attr(smv_el, "cbName"),
                        addresses=_parse_addresses(smv_el),
                    )
                )
            sn.connected_aps.append(cap)
        comm.subnetworks.append(sn)
    return comm


# ---------------------------------------------------------------------------
# IED section
# ---------------------------------------------------------------------------

def _parse_ied(el: etree._Element) -> m.IED:
    ied = m.IED(
        name=_attr(el, "name", ""),
        manufacturer=_attr(el, "manufacturer"),
        type=_attr(el, "type"),
        config_version=_attr(el, "configVersion"),
        desc=_attr(el, "desc"),
    )
    services_el = _child(el, "Services")
    if services_el is not None:
        for svc_el in services_el:
            if isinstance(svc_el.tag, str):
                name = _local(svc_el.tag)
                if name == "Private":
                    continue
                ied.services.append(m.Service(name=name, attrs=dict(svc_el.attrib)))
    for ap_el in _children(el, "AccessPoint"):
        ied.access_points.append(_parse_access_point(ap_el))
    return ied


def _parse_access_point(el: etree._Element) -> m.AccessPoint:
    ap = m.AccessPoint(
        name=_attr(el, "name", ""),
        desc=_attr(el, "desc"),
        router=_attr(el, "router"),
        clock=_attr(el, "clock"),
    )
    server_el = _child(el, "Server")
    if server_el is not None:
        server = m.Server(desc=_attr(server_el, "desc"))
        for ld_el in _children(server_el, "LDevice"):
            server.ldevices.append(_parse_ldevice(ld_el))
        ap.server = server
    return ap


def _parse_ldevice(el: etree._Element) -> m.LDevice:
    ld = m.LDevice(inst=_attr(el, "inst", ""), desc=_attr(el, "desc"))
    ln0_el = _child(el, "LN0")
    if ln0_el is not None:
        ld.ln0 = _parse_logical_node(ln0_el, is_ln0=True)
    for ln_el in _children(el, "LN"):
        ld.lns.append(_parse_logical_node(ln_el, is_ln0=False))
    return ld


def _parse_logical_node(el: etree._Element, is_ln0: bool) -> m.LogicalNode:
    ln = m.LogicalNode(
        ln_class=_attr(el, "lnClass", ""),
        inst=_attr(el, "inst", ""),
        prefix=_attr(el, "prefix"),
        ln_type=_attr(el, "lnType"),
        desc=_attr(el, "desc"),
        is_ln0=is_ln0,
    )
    for doi_el in _children(el, "DOI"):
        ln.doi.append(_parse_doi(doi_el))
    for ds_el in _children(el, "DataSet"):
        ln.datasets.append(_parse_dataset(ds_el))
    for gc_el in _children(el, "GSEControl"):
        ln.gse_controls.append(
            m.GSEControl(
                name=_attr(gc_el, "name", ""),
                app_id=_attr(gc_el, "appID"),
                conf_rev=_attr(gc_el, "confRev"),
                dat_set=_attr(gc_el, "datSet"),
                type=_attr(gc_el, "type", "GOOSE"),
                desc=_attr(gc_el, "desc"),
            )
        )
    for svc_el in _children(el, "SampledValueControl"):
        ln.sv_controls.append(
            m.SampledValueControl(
                name=_attr(svc_el, "name", ""),
                smv_id=_attr(svc_el, "smvID"),
                conf_rev=_attr(svc_el, "confRev"),
                dat_set=_attr(svc_el, "datSet"),
                smp_rate=_attr(svc_el, "smpRate"),
                nof_asdu=_attr(svc_el, "nofASDU"),
                desc=_attr(svc_el, "desc"),
            )
        )
    for rc_el in _children(el, "ReportControl"):
        ln.report_controls.append(
            m.ReportControl(
                name=_attr(rc_el, "name", ""),
                conf_rev=_attr(rc_el, "confRev"),
                dat_set=_attr(rc_el, "datSet"),
                buffered=_attr(rc_el, "buffered", "false") == "true",
                rpt_id=_attr(rc_el, "rptID"),
                buf_time=_attr(rc_el, "bufTime"),
                intg_pd=_attr(rc_el, "intgPd"),
            )
        )
    inputs_el = _child(el, "Inputs")
    if inputs_el is not None:
        for er_el in _children(inputs_el, "ExtRef"):
            ln.ext_refs.append(
                m.ExtRef(
                    int_addr=_attr(er_el, "intAddr"),
                    desc=_attr(er_el, "desc"),
                    iedName=_attr(er_el, "iedName"),
                    ldInst=_attr(er_el, "ldInst"),
                    prefix=_attr(er_el, "prefix"),
                    lnClass=_attr(er_el, "lnClass"),
                    lnInst=_attr(er_el, "lnInst"),
                    doName=_attr(er_el, "doName"),
                    daName=_attr(er_el, "daName"),
                    serviceType=_attr(er_el, "serviceType"),
                    srcLDInst=_attr(er_el, "srcLDInst"),
                    srcPrefix=_attr(er_el, "srcPrefix"),
                    srcLNClass=_attr(er_el, "srcLNClass"),
                    srcLNInst=_attr(er_el, "srcLNInst"),
                    srcCBName=_attr(er_el, "srcCBName"),
                )
            )
    return ln


def _parse_dataset(el: etree._Element) -> m.DataSet:
    ds = m.DataSet(name=_attr(el, "name", ""), desc=_attr(el, "desc"))
    for fcda_el in _children(el, "FCDA"):
        ds.fcda.append(
            m.FCDA(
                ld_inst=_attr(fcda_el, "ldInst"),
                prefix=_attr(fcda_el, "prefix"),
                ln_class=_attr(fcda_el, "lnClass"),
                ln_inst=_attr(fcda_el, "lnInst"),
                do_name=_attr(fcda_el, "doName"),
                da_name=_attr(fcda_el, "daName"),
                fc=_attr(fcda_el, "fc"),
            )
        )
    return ds


def _parse_dai(el: etree._Element) -> m.DAI:
    dai = m.DAI(name=_attr(el, "name", ""), val_kind=_attr(el, "valKind"))
    for val_el in _children(el, "Val"):
        dai.values.append((val_el.text or "").strip())
    for sdi_el in _children(el, "SDI"):
        dai.sdi_children.append(_parse_sdi(sdi_el))
    return dai


def _parse_sdi(el: etree._Element) -> m.SDI:
    sdi = m.SDI(name=_attr(el, "name", ""), ix=_attr(el, "ix"))
    for val_el in _children(el, "Val"):
        sdi.values.append((val_el.text or "").strip())
    for dai_el in _children(el, "DAI"):
        sdi.dai_children.append(_parse_dai(dai_el))
    for child_sdi in _children(el, "SDI"):
        sdi.sdi_children.append(_parse_sdi(child_sdi))
    return sdi


def _parse_doi(el: etree._Element) -> m.DOI:
    doi = m.DOI(name=_attr(el, "name", ""), desc=_attr(el, "desc"))
    for dai_el in _children(el, "DAI"):
        doi.dai_children.append(_parse_dai(dai_el))
    for sdi_el in _children(el, "SDI"):
        doi.sdi_children.append(_parse_sdi(sdi_el))
    return doi


# ---------------------------------------------------------------------------
# DataTypeTemplates section
# ---------------------------------------------------------------------------

def _parse_data_type_templates(el: etree._Element) -> m.DataTypeTemplates:
    dtt = m.DataTypeTemplates()

    for lnt_el in _children(el, "LNodeType"):
        lnt = m.LNodeType(id=_attr(lnt_el, "id", ""), ln_class=_attr(lnt_el, "lnClass", ""), desc=_attr(lnt_el, "desc"))
        for do_el in _children(lnt_el, "DO"):
            lnt.data_objects.append(
                m.DataObjectTemplate(name=_attr(do_el, "name", ""), type_ref=_attr(do_el, "type", ""), desc=_attr(do_el, "desc"))
            )
        dtt.lnode_types[lnt.id] = lnt

    for dot_el in _children(el, "DOType"):
        dot = m.DOType(id=_attr(dot_el, "id", ""), cdc=_attr(dot_el, "cdc", ""), desc=_attr(dot_el, "desc"))
        for da_el in _children(dot_el, "DA"):
            dot.attributes.append(_parse_da_template(da_el, sdo=False))
        for sdo_el in _children(dot_el, "SDO"):
            dot.attributes.append(_parse_da_template(sdo_el, sdo=True))
        dtt.do_types[dot.id] = dot

    for dat_el in _children(el, "DAType"):
        dat = m.DAType(id=_attr(dat_el, "id", ""), desc=_attr(dat_el, "desc"))
        for bda_el in _children(dat_el, "BDA"):
            dat.attributes.append(_parse_da_template(bda_el, sdo=False))
        dtt.da_types[dat.id] = dat

    for et_el in _children(el, "EnumType"):
        et = m.EnumType(id=_attr(et_el, "id", ""), desc=_attr(et_el, "desc"))
        for ev_el in _children(et_el, "EnumVal"):
            et.values.append(m.EnumVal(ord=_attr(ev_el, "ord", ""), text=(ev_el.text or "").strip()))
        dtt.enum_types[et.id] = et

    return dtt


def _parse_da_template(el: etree._Element, sdo: bool) -> m.DataAttributeTemplate:
    return m.DataAttributeTemplate(
        name=_attr(el, "name", ""),
        fc=_attr(el, "fc"),
        b_type=_attr(el, "bType"),
        type_ref=_attr(el, "type"),
        d_chg=_attr(el, "dchg"),
        q_chg=_attr(el, "qchg"),
        d_upd=_attr(el, "dupd"),
        count=_attr(el, "count"),
        val_kind=_attr(el, "valKind"),
        val=el.text.strip() if (not sdo and el.text and el.text.strip()) else None,
        sdo=sdo,
    )
