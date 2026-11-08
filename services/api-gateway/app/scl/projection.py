"""JSON-able projections of a parsed SclDocument."""
from __future__ import annotations

from . import model as m


def to_summary(doc: m.SclDocument) -> dict:
    return {
        "sourcePath": doc.source_path,
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
