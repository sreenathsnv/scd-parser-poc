"""Typed object model for a parsed SCL (SCD/ICD/CID) file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# DataTypeTemplates (type system)
# ---------------------------------------------------------------------------

@dataclass
class EnumVal:
    ord: str
    text: str


@dataclass
class EnumType:
    id: str
    desc: Optional[str]
    values: list[EnumVal] = field(default_factory=list)


@dataclass
class DataAttributeTemplate:
    """A <DA> (inside DOType) or <BDA> (inside DAType)."""
    name: str
    fc: Optional[str]
    b_type: Optional[str]
    type_ref: Optional[str]
    d_chg: Optional[str] = None
    q_chg: Optional[str] = None
    d_upd: Optional[str] = None
    count: Optional[str] = None
    val_kind: Optional[str] = None
    val: Optional[str] = None
    sdo: bool = False  # True if this came from a <SDO> (sub data object) rather than <DA>


@dataclass
class DOType:
    id: str
    cdc: str
    desc: Optional[str]
    attributes: list[DataAttributeTemplate] = field(default_factory=list)


@dataclass
class DAType:
    id: str
    desc: Optional[str]
    attributes: list[DataAttributeTemplate] = field(default_factory=list)


@dataclass
class DataObjectTemplate:
    """A <DO> declaration inside an LNodeType."""
    name: str
    type_ref: str
    desc: Optional[str] = None


@dataclass
class LNodeType:
    id: str
    ln_class: str
    desc: Optional[str]
    data_objects: list[DataObjectTemplate] = field(default_factory=list)


@dataclass
class DataTypeTemplates:
    lnode_types: dict[str, LNodeType] = field(default_factory=dict)
    do_types: dict[str, DOType] = field(default_factory=dict)
    da_types: dict[str, DAType] = field(default_factory=dict)
    enum_types: dict[str, EnumType] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Instance side: IED / AccessPoint / Server / LDevice / LN / DOI / DAI
# ---------------------------------------------------------------------------

@dataclass
class DAI:
    name: str
    val_kind: Optional[str] = None
    values: list[str] = field(default_factory=list)  # usually 0 or 1 <Val>, arrays use ix
    sdi_children: list["SDI"] = field(default_factory=list)


@dataclass
class SDI:
    name: str
    ix: Optional[str] = None
    values: list[str] = field(default_factory=list)
    dai_children: list[DAI] = field(default_factory=list)
    sdi_children: list["SDI"] = field(default_factory=list)


@dataclass
class DOI:
    name: str
    desc: Optional[str] = None
    dai_children: list[DAI] = field(default_factory=list)
    sdi_children: list[SDI] = field(default_factory=list)


@dataclass
class FCDA:
    ld_inst: Optional[str]
    prefix: Optional[str]
    ln_class: Optional[str]
    ln_inst: Optional[str]
    do_name: Optional[str]
    da_name: Optional[str]
    fc: Optional[str]


@dataclass
class DataSet:
    name: str
    desc: Optional[str] = None
    fcda: list[FCDA] = field(default_factory=list)


@dataclass
class GSEControl:
    name: str
    app_id: Optional[str]
    conf_rev: Optional[str]
    dat_set: Optional[str]
    type: str = "GOOSE"
    desc: Optional[str] = None


@dataclass
class SampledValueControl:
    name: str
    smv_id: Optional[str]
    conf_rev: Optional[str]
    dat_set: Optional[str]
    smp_rate: Optional[str]
    nof_asdu: Optional[str]
    desc: Optional[str] = None


@dataclass
class ReportControl:
    name: str
    conf_rev: Optional[str]
    dat_set: Optional[str]
    buffered: bool = False
    rpt_id: Optional[str] = None
    buf_time: Optional[str] = None
    intg_pd: Optional[str] = None


@dataclass
class ExtRef:
    """A subscription endpoint, Edition-1 (value-based) or Edition-2 (service-based)."""
    int_addr: Optional[str] = None
    desc: Optional[str] = None
    # Edition 1 / value-based target fields
    iedName: Optional[str] = None
    ldInst: Optional[str] = None
    prefix: Optional[str] = None
    lnClass: Optional[str] = None
    lnInst: Optional[str] = None
    doName: Optional[str] = None
    daName: Optional[str] = None
    # Edition 2 / service-based target fields
    serviceType: Optional[str] = None
    srcLDInst: Optional[str] = None
    srcPrefix: Optional[str] = None
    srcLNClass: Optional[str] = None
    srcLNInst: Optional[str] = None
    srcCBName: Optional[str] = None


@dataclass
class LogicalNode:
    """<LN0> or <LN>."""
    ln_class: str
    inst: str
    prefix: Optional[str]
    ln_type: Optional[str]
    desc: Optional[str] = None
    is_ln0: bool = False
    doi: list[DOI] = field(default_factory=list)
    datasets: list[DataSet] = field(default_factory=list)
    gse_controls: list[GSEControl] = field(default_factory=list)
    sv_controls: list[SampledValueControl] = field(default_factory=list)
    report_controls: list[ReportControl] = field(default_factory=list)
    ext_refs: list[ExtRef] = field(default_factory=list)

    @property
    def ln_name(self) -> str:
        return f"{self.prefix or ''}{self.ln_class}{self.inst}"


@dataclass
class LDevice:
    inst: str
    desc: Optional[str] = None
    ln0: Optional[LogicalNode] = None
    lns: list[LogicalNode] = field(default_factory=list)

    @property
    def all_lns(self) -> list[LogicalNode]:
        return ([self.ln0] if self.ln0 else []) + self.lns


@dataclass
class Server:
    desc: Optional[str] = None
    ldevices: list[LDevice] = field(default_factory=list)


@dataclass
class AccessPoint:
    name: str
    desc: Optional[str] = None
    router: Optional[str] = None
    clock: Optional[str] = None
    server: Optional[Server] = None


@dataclass
class Service:
    """A bare <Services> child element, e.g. <GOOSE max="0"/>."""
    name: str
    attrs: dict[str, str] = field(default_factory=dict)


@dataclass
class IED:
    name: str
    manufacturer: Optional[str] = None
    type: Optional[str] = None
    config_version: Optional[str] = None
    desc: Optional[str] = None
    access_points: list[AccessPoint] = field(default_factory=list)
    services: list[Service] = field(default_factory=list)

    @property
    def all_ldevices(self) -> list[LDevice]:
        out: list[LDevice] = []
        for ap in self.access_points:
            if ap.server:
                out.extend(ap.server.ldevices)
        return out


# ---------------------------------------------------------------------------
# Substation section (plant topology)
# ---------------------------------------------------------------------------

@dataclass
class LNodeRef:
    """An <LNode> cross-reference inside the Substation section."""
    iedName: Optional[str]
    ldInst: Optional[str]
    prefix: Optional[str]
    lnClass: Optional[str]
    lnInst: Optional[str]


@dataclass
class ConductingEquipment:
    name: str
    type: Optional[str] = None
    desc: Optional[str] = None
    lnodes: list[LNodeRef] = field(default_factory=list)


@dataclass
class Bay:
    name: str
    desc: Optional[str] = None
    conducting_equipment: list[ConductingEquipment] = field(default_factory=list)


@dataclass
class VoltageLevel:
    name: str
    desc: Optional[str] = None
    nom_freq: Optional[str] = None
    num_phases: Optional[str] = None
    bays: list[Bay] = field(default_factory=list)


@dataclass
class Substation:
    name: str
    desc: Optional[str] = None
    voltage_levels: list[VoltageLevel] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Communication section
# ---------------------------------------------------------------------------

@dataclass
class AddressPoint:
    type: str
    value: str


@dataclass
class GSE:
    ld_inst: Optional[str]
    cb_name: Optional[str]
    addresses: list[AddressPoint] = field(default_factory=list)
    min_time: Optional[str] = None
    max_time: Optional[str] = None


@dataclass
class SMV:
    ld_inst: Optional[str]
    cb_name: Optional[str]
    addresses: list[AddressPoint] = field(default_factory=list)


@dataclass
class ConnectedAP:
    ied_name: str
    ap_name: str
    addresses: list[AddressPoint] = field(default_factory=list)
    gse: list[GSE] = field(default_factory=list)
    smv: list[SMV] = field(default_factory=list)

    def address_value(self, p_type: str) -> Optional[str]:
        for a in self.addresses:
            if a.type == p_type:
                return a.value
        return None


@dataclass
class SubNetwork:
    name: str
    type: Optional[str] = None
    desc: Optional[str] = None
    connected_aps: list[ConnectedAP] = field(default_factory=list)


@dataclass
class Communication:
    subnetworks: list[SubNetwork] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Header + root document
# ---------------------------------------------------------------------------

@dataclass
class Header:
    id: str
    version: Optional[str] = None
    revision: Optional[str] = None
    tool_id: Optional[str] = None
    name_structure: Optional[str] = None


@dataclass
class PrivateBlob:
    """Opaque, untouched <Private> subtree, keyed by its type attribute."""
    type: str
    source: object
    parent_path: str


@dataclass
class SclDocument:
    source_path: str
    scl_version: Optional[str]
    scl_revision: Optional[str]
    header: Optional[Header]
    substations: list[Substation] = field(default_factory=list)
    communication: Optional[Communication] = None
    ieds: list[IED] = field(default_factory=list)
    data_type_templates: DataTypeTemplates = field(default_factory=DataTypeTemplates)
    privates: list[PrivateBlob] = field(default_factory=list)

    # original lxml tree, used by the serializer for round-tripping
    _lxml_tree: object = None
    raw_bytes: bytes = b""
    uses_crlf: bool = False
    dirty: bool = False

    def find_ied(self, name: str) -> Optional[IED]:
        for ied in self.ieds:
            if ied.name == name:
                return ied
        return None
