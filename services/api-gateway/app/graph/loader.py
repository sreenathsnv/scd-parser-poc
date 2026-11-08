"""Loads a parsed SclDocument into Neo4j per the schema in schema.py.

Re-ingestion deletes the file's existing subgraph (by sourcePath) first.
Unresolved refs (ExtRef/FCDA) are kept, tagged resolved=false, not dropped.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..scl import model as m
from . import schema as s
from .neo4j_client import ensure_constraints, get_driver


def _k(*parts: str) -> str:
    return "::".join(str(p) for p in parts)


@dataclass
class _Batch:
    source_path: str
    nodes: dict[str, tuple[str, dict]] = field(default_factory=dict)  # key -> (label, props)
    edges: list[tuple[str, str, str, dict]] = field(default_factory=list)  # (from_key, type, to_key, props)

    def node(self, label: str, key: str, **props) -> str:
        props = {k: v for k, v in props.items() if v is not None}
        props["key"] = key
        props["sourcePath"] = self.source_path
        self.nodes[key] = (label, props)
        return key

    def edge(self, from_key: str, edge_type: str, to_key: str, **props) -> None:
        self.edges.append((from_key, edge_type, to_key, props))


def build_batch(doc: m.SclDocument) -> _Batch:
    batch = _Batch(source_path=doc.source_path)
    sp = doc.source_path

    file_key = _k(sp, "SclFile")
    batch.node(
        s.L_FILE,
        file_key,
        headerId=doc.header.id if doc.header else None,
        sclVersion=doc.scl_version,
        sclRevision=doc.scl_revision,
    )

    _load_substations(batch, doc, file_key)
    _load_data_type_templates(batch, doc)
    _load_ieds(batch, doc, file_key)
    _load_communication(batch, doc, file_key)
    _resolve_extrefs(batch, doc)
    _resolve_fcda_references(batch, doc)

    return batch


# ---------------------------------------------------------------------------
# Substation section
# ---------------------------------------------------------------------------

def _load_substations(batch: _Batch, doc: m.SclDocument, file_key: str) -> None:
    sp = doc.source_path
    for sub in doc.substations:
        sub_key = _k(sp, "Substation", sub.name)
        batch.node(s.L_SUBSTATION, sub_key, name=sub.name, desc=sub.desc)
        batch.edge(file_key, s.E_CONTAINS, sub_key)
        for vl in sub.voltage_levels:
            vl_key = _k(sp, "Substation", sub.name, "VoltageLevel", vl.name)
            batch.node(s.L_VOLTAGE_LEVEL, vl_key, name=vl.name, desc=vl.desc, nomFreq=vl.nom_freq, numPhases=vl.num_phases)
            batch.edge(sub_key, s.E_CONTAINS, vl_key)
            for bay in vl.bays:
                bay_key = _k(sp, "Substation", sub.name, "VoltageLevel", vl.name, "Bay", bay.name)
                batch.node(s.L_BAY, bay_key, name=bay.name, desc=bay.desc)
                batch.edge(vl_key, s.E_CONTAINS, bay_key)
                for ce in bay.conducting_equipment:
                    ce_key = _k(sp, "Substation", sub.name, "VoltageLevel", vl.name, "Bay", bay.name, "CE", ce.name)
                    batch.node(s.L_CONDUCTING_EQUIPMENT, ce_key, name=ce.name, type=ce.type, desc=ce.desc)
                    batch.edge(bay_key, s.E_CONTAINS, ce_key)
                    for i, lnode in enumerate(ce.lnodes):
                        lnode_key = _k(ce_key, "LNodeRef", i)
                        batch.node(
                            s.L_LNODE_REF,
                            lnode_key,
                            iedName=lnode.iedName,
                            ldInst=lnode.ldInst,
                            prefix=lnode.prefix,
                            lnClass=lnode.lnClass,
                            lnInst=lnode.lnInst,
                        )
                        batch.edge(ce_key, s.E_CONTAINS, lnode_key)
                        if lnode.iedName and lnode.lnClass is not None:
                            target_ln_key = _k(
                                sp, "IED", lnode.iedName, "LD", lnode.ldInst or "",
                                "LN", lnode.prefix or "", lnode.lnClass, lnode.lnInst or "",
                            )
                            batch.edge(lnode_key, s.E_ASSOCIATED_WITH, target_ln_key, resolved=None)


# ---------------------------------------------------------------------------
# DataTypeTemplates (type system)
# ---------------------------------------------------------------------------

def _load_data_type_templates(batch: _Batch, doc: m.SclDocument) -> None:
    sp = doc.source_path
    dtt = doc.data_type_templates

    for lnt in dtt.lnode_types.values():
        lnt_key = _k(sp, "LNodeType", lnt.id)
        batch.node(s.L_LNODE_TYPE, lnt_key, id=lnt.id, lnClass=lnt.ln_class, desc=lnt.desc)
        for do_tmpl in lnt.data_objects:
            do_key = _k(sp, "LNodeType", lnt.id, "DO", do_tmpl.name)
            batch.node(s.L_DO, do_key, name=do_tmpl.name, desc=do_tmpl.desc, template=True)
            batch.edge(lnt_key, s.E_CONTAINS, do_key)
            dot_key = _k(sp, "DOType", do_tmpl.type_ref)
            batch.edge(do_key, s.E_TYPED_AS, dot_key, resolved=do_tmpl.type_ref in dtt.do_types)

    for dot in dtt.do_types.values():
        dot_key = _k(sp, "DOType", dot.id)
        batch.node(s.L_DO_TYPE, dot_key, id=dot.id, cdc=dot.cdc, desc=dot.desc)
        for da_tmpl in dot.attributes:
            da_key = _k(sp, "DOType", dot.id, "DA", da_tmpl.name)
            batch.node(
                s.L_DA, da_key, name=da_tmpl.name, fc=da_tmpl.fc, bType=da_tmpl.b_type,
                template=True, sdo=da_tmpl.sdo,
            )
            batch.edge(dot_key, s.E_CONTAINS, da_key)
            if da_tmpl.type_ref:
                target_label = s.L_DO_TYPE if da_tmpl.sdo else (s.L_DA_TYPE if da_tmpl.b_type == "Struct" else s.L_ENUM_TYPE)
                target_key = _k(sp, target_label, da_tmpl.type_ref)
                resolved = (
                    da_tmpl.type_ref in dtt.do_types if da_tmpl.sdo
                    else da_tmpl.type_ref in dtt.da_types if da_tmpl.b_type == "Struct"
                    else da_tmpl.type_ref in dtt.enum_types
                )
                batch.edge(da_key, s.E_TYPED_AS, target_key, resolved=resolved)

    for dat in dtt.da_types.values():
        dat_key = _k(sp, "DAType", dat.id)
        batch.node(s.L_DA_TYPE, dat_key, id=dat.id, desc=dat.desc)
        for bda in dat.attributes:
            bda_key = _k(sp, "DAType", dat.id, "BDA", bda.name)
            batch.node(s.L_DA, bda_key, name=bda.name, bType=bda.b_type, template=True)
            batch.edge(dat_key, s.E_CONTAINS, bda_key)

    for et in dtt.enum_types.values():
        et_key = _k(sp, "EnumType", et.id)
        batch.node(
            s.L_ENUM_TYPE, et_key, id=et.id, desc=et.desc,
            values=[f"{v.ord}={v.text}" for v in et.values],
        )


# ---------------------------------------------------------------------------
# IED instance side
# ---------------------------------------------------------------------------

def _load_ieds(batch: _Batch, doc: m.SclDocument, file_key: str) -> None:
    sp = doc.source_path
    for ied in doc.ieds:
        ied_key = _k(sp, "IED", ied.name)
        batch.node(
            s.L_IED, ied_key, name=ied.name, manufacturer=ied.manufacturer,
            type=ied.type, configVersion=ied.config_version, desc=ied.desc,
        )
        batch.edge(file_key, s.E_CONTAINS, ied_key)

        for ap in ied.access_points:
            ap_key = _k(ied_key, "AP", ap.name)
            batch.node(s.L_ACCESS_POINT, ap_key, name=ap.name, desc=ap.desc)
            batch.edge(ied_key, s.E_CONTAINS, ap_key)
            if not ap.server:
                continue
            server_key = _k(ap_key, "Server")
            batch.node(s.L_SERVER, server_key, desc=ap.server.desc)
            batch.edge(ap_key, s.E_CONTAINS, server_key)

            for ld in ap.server.ldevices:
                ld_key = _k(sp, "IED", ied.name, "LD", ld.inst)
                batch.node(s.L_LDEVICE, ld_key, inst=ld.inst, desc=ld.desc)
                batch.edge(server_key, s.E_CONTAINS, ld_key)
                for ln in ld.all_lns:
                    _load_logical_node(batch, doc, ld_key, ied.name, ld.inst, ln)


def _load_logical_node(batch: _Batch, doc: m.SclDocument, ld_key: str, ied_name: str, ld_inst: str, ln: m.LogicalNode) -> None:
    sp = doc.source_path
    ln_key = _k(sp, "IED", ied_name, "LD", ld_inst, "LN", ln.prefix or "", ln.ln_class, ln.inst)
    batch.node(
        s.L_LN, ln_key, lnClass=ln.ln_class, inst=ln.inst, prefix=ln.prefix,
        lnType=ln.ln_type, desc=ln.desc, isLN0=ln.is_ln0, name=ln.ln_name,
    )
    batch.edge(ld_key, s.E_CONTAINS, ln_key)
    if ln.ln_type:
        lnt_key = _k(sp, "LNodeType", ln.ln_type)
        batch.edge(ln_key, s.E_INSTANCE_OF, lnt_key, resolved=ln.ln_type in doc.data_type_templates.lnode_types)

    for doi in ln.doi:
        _load_doi(batch, doc, ln_key, doi)
    for ds in ln.datasets:
        ds_key = _k(ln_key, "DataSet", ds.name)
        batch.node(s.L_DATASET, ds_key, name=ds.name, desc=ds.desc)
        batch.edge(ln_key, s.E_CONTAINS, ds_key)
        for i, fcda in enumerate(ds.fcda):
            fcda_key = _k(ds_key, "FCDA", i)
            batch.node(
                s.L_FCDA, fcda_key, ldInst=fcda.ld_inst, prefix=fcda.prefix, lnClass=fcda.ln_class,
                lnInst=fcda.ln_inst, doName=fcda.do_name, daName=fcda.da_name, fc=fcda.fc,
            )
            batch.edge(ds_key, s.E_HAS_MEMBER, fcda_key)
    for gc in ln.gse_controls:
        gc_key = _k(ln_key, "GSEControl", gc.name)
        batch.node(s.L_GSE_CONTROL, gc_key, name=gc.name, appID=gc.app_id, confRev=gc.conf_rev, type=gc.type, desc=gc.desc)
        batch.edge(ln_key, s.E_CONTAINS, gc_key)
        if gc.dat_set:
            ds_key = _k(ln_key, "DataSet", gc.dat_set)
            batch.edge(gc_key, s.E_PUBLISHES, ds_key, resolved=any(d.name == gc.dat_set for d in ln.datasets))
    for svc in ln.sv_controls:
        svc_key = _k(ln_key, "SampledValueControl", svc.name)
        batch.node(
            s.L_SV_CONTROL, svc_key, name=svc.name, smvID=svc.smv_id, confRev=svc.conf_rev,
            smpRate=svc.smp_rate, nofASDU=svc.nof_asdu, desc=svc.desc,
        )
        batch.edge(ln_key, s.E_CONTAINS, svc_key)
        if svc.dat_set:
            ds_key = _k(ln_key, "DataSet", svc.dat_set)
            batch.edge(svc_key, s.E_PUBLISHES, ds_key, resolved=any(d.name == svc.dat_set for d in ln.datasets))
    for rc in ln.report_controls:
        rc_key = _k(ln_key, "ReportControl", rc.name)
        batch.node(
            s.L_REPORT_CONTROL, rc_key, name=rc.name, confRev=rc.conf_rev, buffered=rc.buffered,
            rptID=rc.rpt_id, bufTime=rc.buf_time, intgPd=rc.intg_pd,
        )
        batch.edge(ln_key, s.E_CONTAINS, rc_key)
        if rc.dat_set:
            ds_key = _k(ln_key, "DataSet", rc.dat_set)
            batch.edge(rc_key, s.E_PUBLISHES, ds_key, resolved=any(d.name == rc.dat_set for d in ln.datasets))


def _load_doi(batch: _Batch, doc: m.SclDocument, parent_key: str, doi: m.DOI) -> None:
    doi_key = _k(parent_key, "DOI", doi.name)
    batch.node(s.L_DO, doi_key, name=doi.name, desc=doi.desc, template=False)
    batch.edge(parent_key, s.E_CONTAINS, doi_key)
    for dai in doi.dai_children:
        _load_dai(batch, doi_key, dai)
    for sdi in doi.sdi_children:
        _load_sdi(batch, doi_key, sdi)


def _load_sdi(batch: _Batch, parent_key: str, sdi: m.SDI) -> None:
    sdi_key = _k(parent_key, "SDI", sdi.name, sdi.ix or "")
    batch.node(s.L_DO, sdi_key, name=sdi.name, ix=sdi.ix, template=False)
    batch.edge(parent_key, s.E_CONTAINS, sdi_key)
    for dai in sdi.dai_children:
        _load_dai(batch, sdi_key, dai)
    for child in sdi.sdi_children:
        _load_sdi(batch, sdi_key, child)


def _load_dai(batch: _Batch, parent_key: str, dai: m.DAI) -> None:
    dai_key = _k(parent_key, "DAI", dai.name)
    batch.node(
        s.L_DA, dai_key, name=dai.name, valKind=dai.val_kind, template=False,
        val=dai.values[0] if dai.values else None,
    )
    batch.edge(parent_key, s.E_CONTAINS, dai_key)
    for sdi in dai.sdi_children:
        _load_sdi(batch, dai_key, sdi)


# ---------------------------------------------------------------------------
# Communication section
# ---------------------------------------------------------------------------

def _load_communication(batch: _Batch, doc: m.SclDocument, file_key: str) -> None:
    if not doc.communication:
        return
    sp = doc.source_path
    for sn in doc.communication.subnetworks:
        sn_key = _k(sp, "SubNetwork", sn.name)
        batch.node(s.L_SUBNETWORK, sn_key, name=sn.name, type=sn.type, desc=sn.desc)
        batch.edge(file_key, s.E_CONTAINS, sn_key)
        for cap in sn.connected_aps:
            cap_key = _k(sn_key, "ConnectedAP", cap.ied_name, cap.ap_name)
            batch.node(
                s.L_CONNECTED_AP, cap_key, iedName=cap.ied_name, apName=cap.ap_name,
                ipAddr=cap.address_value("IP"), ipSubnet=cap.address_value("IP-SUBNET"),
                ipGateway=cap.address_value("IP-GATEWAY"),
            )
            batch.edge(sn_key, s.E_CONTAINS, cap_key)
            ied_key = _k(sp, "IED", cap.ied_name)
            batch.edge(cap_key, s.E_ON, sn_key)
            batch.edge(ied_key, "CONNECTED_VIA", cap_key, resolved=any(i.name == cap.ied_name for i in doc.ieds))


# ---------------------------------------------------------------------------
# Resolution passes
# ---------------------------------------------------------------------------

def _resolve_extrefs(batch: _Batch, doc: m.SclDocument) -> None:
    sp = doc.source_path
    ied_names = {i.name for i in doc.ieds}
    for ied in doc.ieds:
        for ld in ied.all_ldevices:
            for ln in ld.all_lns:
                ln_key = _k(sp, "IED", ied.name, "LD", ld.inst, "LN", ln.prefix or "", ln.ln_class, ln.inst)
                for i, ext_ref in enumerate(ln.ext_refs):
                    if not ext_ref.iedName:
                        continue
                    resolved = ext_ref.iedName in ied_names
                    if ext_ref.serviceType in ("GOOSE", "SMV") and ext_ref.srcCBName:
                        target_ln_key = _k(
                            sp, "IED", ext_ref.iedName, "LD", ext_ref.srcLDInst or "",
                            "LN", "", "LLN0", "",
                        )
                        target_key = _k(target_ln_key, ("GSEControl" if ext_ref.serviceType == "GOOSE" else "SampledValueControl"), ext_ref.srcCBName)
                    else:
                        target_key = _k(
                            sp, "IED", ext_ref.iedName, "LD", ext_ref.ldInst or "",
                            "LN", ext_ref.prefix or "", ext_ref.lnClass or "", ext_ref.lnInst or "",
                        )
                        if ext_ref.doName:
                            target_key = _k(target_key, "DOI", ext_ref.doName)
                            if ext_ref.daName:
                                target_key = _k(target_key, "DAI", ext_ref.daName)
                    batch.edge(
                        ln_key, s.E_SUBSCRIBES_TO, target_key,
                        resolved=resolved, intAddr=ext_ref.int_addr, extRefIndex=i,
                    )


def _resolve_fcda_references(batch: _Batch, doc: m.SclDocument) -> None:
    sp = doc.source_path
    for ied in doc.ieds:
        for ld in ied.all_ldevices:
            doi_names_by_ln = {
                (ln.prefix or "", ln.ln_class, ln.inst): {doi.name for doi in ln.doi} for ln in ld.all_lns
            }
            for ln in ld.all_lns:
                for ds in ln.datasets:
                    ds_key = _k(sp, "IED", ied.name, "LD", ld.inst, "LN", ln.prefix or "", ln.ln_class, ln.inst, "DataSet", ds.name)
                    for i, fcda in enumerate(ds.fcda):
                        fcda_key = _k(ds_key, "FCDA", i)
                        target_ld_inst = fcda.ld_inst or ld.inst
                        key_tuple = (fcda.prefix or "", fcda.ln_class or "", fcda.ln_inst or "")
                        known_dois = doi_names_by_ln.get(key_tuple, set())
                        resolved = fcda.do_name in known_dois if fcda.do_name else False
                        target_key = _k(
                            sp, "IED", ied.name, "LD", target_ld_inst, "LN",
                            fcda.prefix or "", fcda.ln_class or "", fcda.ln_inst or "",
                        )
                        if fcda.do_name:
                            target_key = _k(target_key, "DOI", fcda.do_name)
                            if fcda.da_name:
                                target_key = _k(target_key, "DAI", fcda.da_name)
                        batch.edge(fcda_key, s.E_REFERENCES, target_key, resolved=resolved)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def delete_file_subgraph(source_path: str) -> None:
    driver = get_driver()
    with driver.session() as session:
        session.run(f"MATCH (n:{s.COMMON_LABEL} {{sourcePath: $sp}}) DETACH DELETE n", sp=source_path)


def ingest(doc: m.SclDocument) -> dict:
    ensure_constraints()  # idempotent; self-heals if Neo4j wasn't up at app startup
    batch = build_batch(doc)
    driver = get_driver()
    with driver.session() as session:
        session.run(f"MATCH (n:{s.COMMON_LABEL} {{sourcePath: $sp}}) DETACH DELETE n", sp=doc.source_path)

        nodes_by_label: dict[str, list[dict]] = {}
        for key, (label, props) in batch.nodes.items():
            nodes_by_label.setdefault(label, []).append(props)
        for label, props_list in nodes_by_label.items():
            session.run(
                f"UNWIND $rows AS row MERGE (n:{s.COMMON_LABEL}:{label} {{key: row.key}}) SET n += row",
                rows=props_list,
            )

        edges_by_type: dict[str, list[dict]] = {}
        for from_key, edge_type, to_key, props in batch.edges:
            edges_by_type.setdefault(edge_type, []).append({"from": from_key, "to": to_key, **props})
        for edge_type, rows in edges_by_type.items():
            # :Node label keeps this MERGE indexed; a dangling target gets a placeholder node
            session.run(
                f"""
                UNWIND $rows AS row
                MERGE (a:{s.COMMON_LABEL} {{key: row.from}})
                MERGE (b:{s.COMMON_LABEL} {{key: row.to}})
                MERGE (a)-[r:{edge_type}]->(b)
                SET r += row
                """,
                rows=rows,
            )

    return {
        "source_path": doc.source_path,
        "node_count": len(batch.nodes),
        "edge_count": len(batch.edges),
    }
