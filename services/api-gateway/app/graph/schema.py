"""Node/edge label constants and Neo4j schema setup."""
from __future__ import annotations

# Node labels
L_FILE = "SclFile"
L_SUBSTATION = "Substation"
L_VOLTAGE_LEVEL = "VoltageLevel"
L_BAY = "Bay"
L_CONDUCTING_EQUIPMENT = "ConductingEquipment"
L_LNODE_REF = "LNodeRef"
L_IED = "IED"
L_ACCESS_POINT = "AccessPoint"
L_SERVER = "Server"
L_LDEVICE = "LDevice"
L_LN = "LogicalNode"
L_DO = "DataObject"
L_DA = "DataAttribute"
L_LNODE_TYPE = "LNodeType"
L_DO_TYPE = "DOType"
L_DA_TYPE = "DAType"
L_ENUM_TYPE = "EnumType"
L_SUBNETWORK = "SubNetwork"
L_CONNECTED_AP = "ConnectedAP"
L_DATASET = "DataSet"
L_FCDA = "FCDA"
L_GSE_CONTROL = "GSEControl"
L_SV_CONTROL = "SampledValueControl"
L_REPORT_CONTROL = "ReportControl"

ALL_NODE_LABELS = [
    L_FILE, L_SUBSTATION, L_VOLTAGE_LEVEL, L_BAY, L_CONDUCTING_EQUIPMENT, L_LNODE_REF,
    L_IED, L_ACCESS_POINT, L_SERVER, L_LDEVICE, L_LN, L_DO, L_DA,
    L_LNODE_TYPE, L_DO_TYPE, L_DA_TYPE, L_ENUM_TYPE,
    L_SUBNETWORK, L_CONNECTED_AP, L_DATASET, L_FCDA,
    L_GSE_CONTROL, L_SV_CONTROL, L_REPORT_CONTROL,
]

# Edge types
E_CONTAINS = "CONTAINS"
E_INSTANCE_OF = "INSTANCE_OF"
E_TYPED_AS = "TYPED_AS"
E_ASSOCIATED_WITH = "ASSOCIATED_WITH"
E_HAS_MEMBER = "HAS_MEMBER"
E_REFERENCES = "REFERENCES"
E_PUBLISHES = "PUBLISHES"
E_SUBSCRIBES_TO = "SUBSCRIBES_TO"
E_ON = "ON"


# every node also gets this label, so edge-endpoint MERGEs (which don't
# always know the specific label of the other end) still hit an index
COMMON_LABEL = "Node"


def constraint_statements() -> list[str]:
    labels = ALL_NODE_LABELS + [COMMON_LABEL]
    return [f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.key IS UNIQUE" for label in labels]


def index_statements() -> list[str]:
    return [f"CREATE INDEX IF NOT EXISTS FOR (n:{COMMON_LABEL}) ON (n.sourcePath)"]
