"""Custom data-quality checks that XSD/OCL validation does not cover:
9.2.6 naming uniqueness, duplicate IP/MAC, empty control blocks, dangling
refs, and missing Substation (.scd files only -- not expected on .icd/.cid).
"""
from __future__ import annotations

import os
from collections import defaultdict

from ..scl import model as m
from .schemas import Severity, ValidationReport

PLACEHOLDER_IPS = {"0.0.0.0"}


def run_all(doc: m.SclDocument) -> ValidationReport:
    report = ValidationReport(source_path=doc.source_path)
    check_naming_uniqueness_9_2_6(doc, report)
    check_duplicate_ip_mac(doc, report)
    check_empty_control_blocks(doc, report)
    check_missing_substation(doc, report)
    check_dangling_lntype(doc, report)
    check_dangling_extref(doc, report)
    return report


def check_naming_uniqueness_9_2_6(doc: m.SclDocument, report: ValidationReport) -> None:
    """Clause 9.2.6: LN (prefix+lnClass+inst) unique per LDevice; LDevice.inst unique per Server."""
    for ied in doc.ieds:
        for ap in ied.access_points:
            if not ap.server:
                continue
            seen_ld_inst: dict[str, int] = defaultdict(int)
            for ld in ap.server.ldevices:
                seen_ld_inst[ld.inst] += 1
                seen_ln: dict[tuple[str, str, str], int] = defaultdict(int)
                for ln in ld.all_lns:
                    key = (ln.prefix or "", ln.ln_class, ln.inst)
                    seen_ln[key] += 1
                for (prefix, ln_class, inst), count in seen_ln.items():
                    if count > 1:
                        report.add(
                            rule="naming-uniqueness-9.2.6",
                            severity=Severity.ERROR,
                            message=(
                                f"IED '{ied.name}' LDevice '{ld.inst}' has {count} logical nodes "
                                f"named '{prefix}{ln_class}{inst}' — LN names must be unique within an LDevice"
                            ),
                            path=f"IED[{ied.name}]/LDevice[{ld.inst}]",
                            ied=ied.name,
                            ldInst=ld.inst,
                            lnName=f"{prefix}{ln_class}{inst}",
                        )
            for ld_inst, count in seen_ld_inst.items():
                if count > 1:
                    report.add(
                        rule="naming-uniqueness-9.2.6",
                        severity=Severity.ERROR,
                        message=(
                            f"IED '{ied.name}' AccessPoint '{ap.name}' has {count} LDevices "
                            f"with inst='{ld_inst}' — LDevice inst must be unique per Server"
                        ),
                        path=f"IED[{ied.name}]/AccessPoint[{ap.name}]",
                        ied=ied.name,
                        ldInst=ld_inst,
                    )


def check_duplicate_ip_mac(doc: m.SclDocument, report: ValidationReport) -> None:
    if not doc.communication:
        return
    for sn in doc.communication.subnetworks:
        by_ip: dict[str, list[str]] = defaultdict(list)
        by_mac: dict[str, list[str]] = defaultdict(list)
        for cap in sn.connected_aps:
            ip = cap.address_value("IP")
            if ip:
                by_ip[ip].append(cap.ied_name)
            for gse in cap.gse:
                mac = next((a.value for a in gse.addresses if a.type == "MAC-Address"), None)
                if mac:
                    by_mac[mac].append(f"{cap.ied_name}/{gse.cb_name or ''}")

        for ip, ied_names in by_ip.items():
            if len(ied_names) <= 1:
                continue
            if ip in PLACEHOLDER_IPS:
                report.add(
                    rule="duplicate-ip",
                    severity=Severity.INFO,
                    message=(
                        f"SubNetwork '{sn.name}': {len(ied_names)} IEDs share placeholder address "
                        f"{ip} ({', '.join(ied_names)}) — likely unconfigured, not necessarily a conflict"
                    ),
                    path=f"Communication/SubNetwork[{sn.name}]",
                    subnetwork=sn.name,
                    ip=ip,
                    ieds=ied_names,
                )
                continue
            report.add(
                rule="duplicate-ip",
                severity=Severity.ERROR,
                message=(
                    f"SubNetwork '{sn.name}': {len(ied_names)} IEDs share IP address {ip} "
                    f"({', '.join(ied_names)}) — addresses must be unique within a SubNetwork"
                ),
                path=f"Communication/SubNetwork[{sn.name}]",
                subnetwork=sn.name,
                ip=ip,
                ieds=ied_names,
            )

        for mac, endpoints in by_mac.items():
            if len(endpoints) <= 1:
                continue
            report.add(
                rule="duplicate-mac",
                severity=Severity.ERROR,
                message=(
                    f"SubNetwork '{sn.name}': {len(endpoints)} GOOSE publishers share MAC address {mac} "
                    f"({', '.join(endpoints)})"
                ),
                path=f"Communication/SubNetwork[{sn.name}]",
                subnetwork=sn.name,
                mac=mac,
                endpoints=endpoints,
            )


def check_empty_control_blocks(doc: m.SclDocument, report: ValidationReport) -> None:
    for ied in doc.ieds:
        for ld in ied.all_ldevices:
            datasets_by_name = {ds.name: ds for ln in ld.all_lns for ds in ln.datasets}
            for ln in ld.all_lns:
                for gc in ln.gse_controls:
                    _check_control_block(report, ied, ld, ln, "GSEControl", gc.name, gc.dat_set, datasets_by_name)
                for svc in ln.sv_controls:
                    _check_control_block(report, ied, ld, ln, "SampledValueControl", svc.name, svc.dat_set, datasets_by_name)
                for rc in ln.report_controls:
                    _check_control_block(report, ied, ld, ln, "ReportControl", rc.name, rc.dat_set, datasets_by_name)


def _check_control_block(
    report: ValidationReport,
    ied: m.IED,
    ld: m.LDevice,
    ln: m.LogicalNode,
    kind: str,
    name: str,
    dat_set: str | None,
    datasets_by_name: dict[str, m.DataSet],
) -> None:
    path = f"IED[{ied.name}]/LDevice[{ld.inst}]/{ln.ln_name}/{kind}[{name}]"
    if not dat_set:
        report.add(
            rule="empty-control-block",
            severity=Severity.WARNING,
            message=f"{kind} '{name}' on {ied.name}/{ld.inst}/{ln.ln_name} has no datSet configured",
            path=path,
            ied=ied.name,
            controlBlock=name,
            kind=kind,
        )
        return
    ds = datasets_by_name.get(dat_set)
    if ds is None:
        report.add(
            rule="empty-control-block",
            severity=Severity.ERROR,
            message=(
                f"{kind} '{name}' on {ied.name}/{ld.inst}/{ln.ln_name} references datSet "
                f"'{dat_set}' which does not exist in that LDevice"
            ),
            path=path,
            ied=ied.name,
            controlBlock=name,
            kind=kind,
            datSet=dat_set,
        )
    elif len(ds.fcda) == 0:
        report.add(
            rule="empty-control-block",
            severity=Severity.WARNING,
            message=(
                f"{kind} '{name}' on {ied.name}/{ld.inst}/{ln.ln_name} publishes datSet "
                f"'{dat_set}' which has zero FCDA members"
            ),
            path=path,
            ied=ied.name,
            controlBlock=name,
            kind=kind,
            datSet=dat_set,
        )


def check_missing_substation(doc: m.SclDocument, report: ValidationReport) -> None:
    ext = os.path.splitext(doc.source_path)[1].lower()
    if ext != ".scd":
        return
    if len(doc.substations) == 0:
        report.add(
            rule="missing-substation",
            severity=Severity.ERROR,
            message=(
                "This is an .scd (system-level Substation Configuration Description) file but defines "
                "no <Substation> section — plant topology (VoltageLevel/Bay/ConductingEquipment) is missing"
            ),
            path="SCL",
        )


def check_dangling_lntype(doc: m.SclDocument, report: ValidationReport) -> None:
    lnode_types = doc.data_type_templates.lnode_types
    do_types = doc.data_type_templates.do_types
    for ied in doc.ieds:
        for ld in ied.all_ldevices:
            for ln in ld.all_lns:
                if not ln.ln_type:
                    continue
                lnt = lnode_types.get(ln.ln_type)
                if lnt is None:
                    report.add(
                        rule="dangling-lntype",
                        severity=Severity.ERROR,
                        message=(
                            f"LN '{ln.ln_name}' on {ied.name}/{ld.inst} references lnType "
                            f"'{ln.ln_type}' which has no matching <LNodeType id=\"...\"> in DataTypeTemplates"
                        ),
                        path=f"IED[{ied.name}]/LDevice[{ld.inst}]/{ln.ln_name}",
                        ied=ied.name,
                        lnType=ln.ln_type,
                    )
                    continue
                for do_tmpl in lnt.data_objects:
                    if do_tmpl.type_ref not in do_types:
                        report.add(
                            rule="dangling-lntype",
                            severity=Severity.ERROR,
                            message=(
                                f"LNodeType '{lnt.id}' DO '{do_tmpl.name}' references DOType "
                                f"'{do_tmpl.type_ref}' which does not exist"
                            ),
                            path=f"DataTypeTemplates/LNodeType[{lnt.id}]/DO[{do_tmpl.name}]",
                            lnodeType=lnt.id,
                            doType=do_tmpl.type_ref,
                        )


def check_dangling_extref(doc: m.SclDocument, report: ValidationReport) -> None:
    ied_names = {ied.name for ied in doc.ieds}
    for ied in doc.ieds:
        for ld in ied.all_ldevices:
            for ln in ld.all_lns:
                for ext_ref in ln.ext_refs:
                    target = ext_ref.iedName
                    if not target:
                        continue  # unconnected ExtRef template, not an error by itself
                    if target not in ied_names:
                        report.add(
                            rule="dangling-extref",
                            severity=Severity.ERROR,
                            message=(
                                f"ExtRef on {ied.name}/{ld.inst}/{ln.ln_name} (intAddr='{ext_ref.int_addr}') "
                                f"references iedName='{target}' which does not exist in this file"
                            ),
                            path=f"IED[{ied.name}]/LDevice[{ld.inst}]/{ln.ln_name}/Inputs/ExtRef",
                            ied=ied.name,
                            targetIed=target,
                        )
