"""JSON-able projections of a parsed SclDocument."""
from __future__ import annotations

from . import model as m


def to_summary(doc: m.SclDocument) -> dict:
    return {
        "sourcePath": doc.source_path,
        "dirty": doc.unsaved,
        "sclVersion": doc.scl_version,
        "sclRevision": doc.scl_revision,
        "header": (
            {"id": doc.header.id, "version": doc.header.version, "revision": doc.header.revision}
            if doc.header
            else None
        ),
        "substationCount": len(doc.substations),
        "iedCount": len(doc.ieds),
        "subNetworkCount": len(doc.communication.subnetworks) if doc.communication else 0,
        "lnodeTypeCount": len(doc.data_type_templates.lnode_types),
        "doTypeCount": len(doc.data_type_templates.do_types),
        "ieds": [to_ied_summary(ied) for ied in doc.ieds],
    }


def to_ied_summary(ied: m.IED) -> dict:
    ldevices = ied.all_ldevices
    return {
        "name": ied.name,
        "manufacturer": ied.manufacturer,
        "type": ied.type,
        "ldeviceCount": len(ldevices),
        "lnCount": sum(len(ld.all_lns) for ld in ldevices),
        "ldevices": [
            {
                "inst": ld.inst,
                "lnCount": len(ld.all_lns),
                "logicalNodes": [
                    {
                        "name": ln.ln_name,
                        "lnClass": ln.ln_class,
                        "lnType": ln.ln_type,
                        "doiCount": len(ln.doi),
                        "datasetCount": len(ln.datasets),
                        "gseControlCount": len(ln.gse_controls),
                        "svControlCount": len(ln.sv_controls),
                        "reportControlCount": len(ln.report_controls),
                        "extRefCount": len(ln.ext_refs),
                    }
                    for ln in ld.all_lns
                ],
            }
            for ld in ldevices
        ],
    }


def to_tree(doc: m.SclDocument) -> dict:
    dtt = doc.data_type_templates
    return {
        "substations": [_substation_node(sub) for sub in doc.substations],
        "ieds": [_ied_node(ied, dtt) for ied in doc.ieds],
    }


def _node(id_: str, label: str, kind: str, attrs: dict, children: list) -> dict:
    return {"id": id_, "label": label, "kind": kind, "attrs": attrs, "children": children}


def _substation_node(sub: m.Substation) -> dict:
    return _node(
        f"sub::{sub.name}", sub.name, "Substation", {"desc": sub.desc},
        [_voltage_level_node(sub.name, vl) for vl in sub.voltage_levels],
    )


def _voltage_level_node(sub_name: str, vl: m.VoltageLevel) -> dict:
    id_ = f"sub::{sub_name}::vl::{vl.name}"
    return _node(id_, vl.name, "VoltageLevel", {"nomFreq": vl.nom_freq, "numPhases": vl.num_phases}, [
        _bay_node(id_, bay) for bay in vl.bays
    ])


def _bay_node(vl_id: str, bay: m.Bay) -> dict:
    id_ = f"{vl_id}::bay::{bay.name}"
    return _node(id_, bay.name, "Bay", {"desc": bay.desc}, [
        _conducting_equipment_node(id_, ce) for ce in bay.conducting_equipment
    ])


def _conducting_equipment_node(bay_id: str, ce: m.ConductingEquipment) -> dict:
    id_ = f"{bay_id}::ce::{ce.name}"
    children = [
        _node(f"{id_}::lnode::{i}", f"{ln.prefix or ''}{ln.lnClass}{ln.lnInst or ''}", "LNodeRef",
              {"iedName": ln.iedName, "ldInst": ln.ldInst, "lnClass": ln.lnClass}, [])
        for i, ln in enumerate(ce.lnodes)
    ]
    return _node(id_, ce.name, "ConductingEquipment", {"type": ce.type, "desc": ce.desc}, children)


def _ied_node(ied: m.IED, dtt: m.DataTypeTemplates) -> dict:
    id_ = f"ied::{ied.name}"
    children = [_access_point_node(id_, ap, dtt, ied.name) for ap in ied.access_points]
    return _node(id_, ied.name, "IED", {"manufacturer": ied.manufacturer, "type": ied.type}, children)


def _access_point_node(ied_id: str, ap: m.AccessPoint, dtt: m.DataTypeTemplates, ied_name: str) -> dict:
    id_ = f"{ied_id}::ap::{ap.name}"
    children = []
    if ap.server:
        server_id = f"{id_}::server"
        ld_children = [_ldevice_node(server_id, ld, dtt, ied_name) for ld in ap.server.ldevices]
        children = [_node(server_id, "Server", "Server", {}, ld_children)]
    return _node(id_, ap.name, "AccessPoint", {}, children)


def _ldevice_node(server_id: str, ld: m.LDevice, dtt: m.DataTypeTemplates, ied_name: str) -> dict:
    id_ = f"{server_id}::ld::{ld.inst}"
    children = [_ln_node(id_, ln, dtt, ied_name, ld.inst) for ln in ld.all_lns]
    return _node(id_, ld.inst, "LDevice", {"desc": ld.desc}, children)


def _do_type_map(dtt: m.DataTypeTemplates, lnode_type_id: str | None) -> dict[str, m.DataObjectTemplate]:
    lnt = dtt.lnode_types.get(lnode_type_id) if lnode_type_id else None
    if not lnt:
        return {}
    return {do.name: do for do in lnt.data_objects}


def _da_type_map(dtt: m.DataTypeTemplates, do_type_id: str | None) -> dict[str, m.DataAttributeTemplate]:
    dot = dtt.do_types.get(do_type_id) if do_type_id else None
    if not dot:
        return {}
    return {da.name: da for da in dot.attributes}


def _ln_node(ld_id: str, ln: m.LogicalNode, dtt: m.DataTypeTemplates, ied_name: str, ld_inst: str) -> dict:
    id_ = f"{ld_id}::ln::{ln.prefix or ''}{ln.ln_class}{ln.inst}"
    do_map = _do_type_map(dtt, ln.ln_type)
    edit_ctx = {
        "iedName": ied_name, "ldInst": ld_inst,
        "lnPrefix": ln.prefix or "", "lnClass": ln.ln_class, "lnInst": ln.inst,
    }
    children = [_doi_node(id_, doi, do_map, dtt, edit_ctx, []) for doi in ln.doi]
    attrs = {
        "lnClass": ln.ln_class, "inst": ln.inst, "prefix": ln.prefix, "lnType": ln.ln_type,
        "lnTypeResolved": ln.ln_type in dtt.lnode_types if ln.ln_type else None,
        "datasetCount": len(ln.datasets), "gseControlCount": len(ln.gse_controls),
        "reportControlCount": len(ln.report_controls), "extRefCount": len(ln.ext_refs),
    }
    return _node(id_, ln.ln_name, "LogicalNode", attrs, children)


def _doi_node(ln_id: str, doi: m.DOI, do_map: dict, dtt: m.DataTypeTemplates, edit_ctx: dict, doi_path: list[str]) -> dict:
    id_ = f"{ln_id}::doi::{doi.name}"
    path = doi_path + [doi.name]
    do_tmpl = do_map.get(doi.name)
    do_type = dtt.do_types.get(do_tmpl.type_ref) if do_tmpl else None
    da_map = _da_type_map(dtt, do_tmpl.type_ref) if do_tmpl else {}
    children = [_dai_node(id_, dai, da_map, edit_ctx, path) for dai in doi.dai_children]
    children += [_sdi_node(id_, sdi, dtt, edit_ctx, path) for sdi in doi.sdi_children]
    attrs = {"desc": doi.desc, "cdc": do_type.cdc if do_type else None, "resolved": do_tmpl is not None}
    return _node(id_, doi.name, "DataObject", attrs, children)


def _sdi_node(parent_id: str, sdi: m.SDI, dtt: m.DataTypeTemplates, edit_ctx: dict, doi_path: list[str]) -> dict:
    id_ = f"{parent_id}::sdi::{sdi.name}"
    path = doi_path + [sdi.name]
    children = [_dai_node(id_, dai, {}, edit_ctx, path) for dai in sdi.dai_children]
    children += [_sdi_node(id_, child, dtt, edit_ctx, path) for child in sdi.sdi_children]
    return _node(id_, sdi.name, "DataObject", {"ix": sdi.ix}, children)


def _dai_node(doi_id: str, dai: m.DAI, da_map: dict, edit_ctx: dict, doi_path: list[str]) -> dict:
    id_ = f"{doi_id}::dai::{dai.name}"
    da_tmpl = da_map.get(dai.name)
    attrs = {
        "val": dai.values[0] if dai.values else None,
        "valKind": dai.val_kind,
        "fc": da_tmpl.fc if da_tmpl else None,
        "bType": da_tmpl.b_type if da_tmpl else None,
        "resolved": da_tmpl is not None,
        "editable": True,
        **edit_ctx,
        "doiPath": doi_path,
        "daiName": dai.name,
    }
    return _node(id_, dai.name, "DataAttribute", attrs, [])
