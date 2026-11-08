# Plan: IEC 61850 Standard Signal References — Research Notes

**Status note (plan mode):** Plan mode restricts me to read-only actions plus edits to this plan file. I therefore could not run the `Write` tool against the requested output path:

`D:\Trivium-Inhouse\SCD-POC\research_notes\IEC 61850 SCL formats and tools\signal_references.md`

Research was completed using WebSearch/WebFetch (read-only). The full notes are compiled below in the exact format requested by the research assignment. Once you exit plan mode (or approve this plan), my next step is simply: `Write` this content (everything under the `---` divider) to the target path above, unchanged.

All sources below are secondary (vendor manuals, standards-body issue trackers, tutorials, blogs) because the IEC 61850 parts themselves are paywalled standards not available via web search/fetch. Every normative-sounding claim is attributed to the secondary source that reported it, and gaps are flagged explicitly where the primary standard text could not be verified.

---

# IEC 61850 Standard Signal References — Object References, FCDA, and Naming Conventions

## What is an "object reference" per IEC 61850-7-2/-7-1 (general addressing model)?

### Takeaway
An IEC 61850 object reference is a hierarchical path string that addresses a specific node in the data model — Server → Logical Device (LD) → Logical Node (LN) → Data Object (DO, with optional nested sub-DOs) → Data Attribute (DA, with optional nested sub-DAs) — built by concatenating name parts with `/` (between LD and LN) and `.` (between LN/DO/DA levels); the reference does not have to terminate at a leaf attribute, it can stop at any DO level and implicitly cover everything beneath it.

### Cited Findings
- IEC 61850-7-1 introduces the conceptual classes SERVER, LOGICAL-DEVICE (LD), LOGICAL-NODE (LN) and DATA, which form the addressing hierarchy that object references walk — [IEC 61850-7-1 2011 standard listing](https://standards.iteh.ai/catalog/standards/iec/5e0b3350-e48c-436f-9f02-4b962c81cd0b/iec-61850-7-1-2011)
- A documented reference example `IED1LD1/3phMMXU1.A.phsA.cVal.mag.f` splits as: everything before `/` = logical device portion; everything up to the first `.` after the slash = the logical node portion (prefix `3ph` + class `MMXU` + instance `1`); everything after = the data reference path (`A.phsA.cVal.mag.f`) — [LF Energy / OpenSCD wiki](https://lf-energy.atlassian.net/wiki/spaces/SHP/pages/154009785)
- "The endpoint must not necessarily be the leaf data attribute" — a reference can point at a Data Object and thereby designate the whole subtree beneath it — [LF Energy wiki](https://lf-energy.atlassian.net/wiki/spaces/SHP/pages/154009785)
- A Beckhoff TwinCAT IEC 61850 implementation's `GetObjectReference()` API confirms the separator rules precisely with a concrete model: IED `MA2C03`, LD `MA2C03Relay`, LN `LLN0`, DO `Mod`, DA `stVal` → the returned reference strings are: IED → `MA2C03`; LD → `MA2C03Relay`; LN → `MA2C03Relay/LLN0`; DO → `MA2C03Relay/LLN0.Mod`; DA → `MA2C03Relay/LLN0.Mod.stVal`. This also demonstrates that objects above LN level never include the server/IED name repeated, and objects above LN never include a functional-constraint/group name in the path — [Beckhoff infosys TF6510 TC3 IEC61850 docs](https://infosys.beckhoff.com/content/1033/tf6510_tc3_iec61850/5662798219.html)
- A widely used simplified example from an IEC 61850 tutorial deck: MMS-style reference `IED:Relay1/XCBR2.CO.Pos` (IED name, colon, then LD/LN.FC.DO) — [Scribd "IEC 61850 Tutorial"](https://www.scribd.com/doc/251026189/IEC-61850-Tutorial-pdf)
- ABB's IEC 61850 server documentation gives a plain dot-path example for a data attribute: `CSWI.Pos.stVal` (LN.DO.DA, without LD/IED prefix shown since it is accessed in-context of a given server/LD) — [ABB help.plc.abb.com](https://en.help.plc.abb.com/iec_61850_server_introduction.html)

### Inferences
- The formal (informal) grammar implied by all sources is:
  `ObjectReference ::= IEDName LDInst "/" [ LNPrefix ] LNClass LNInst "." DOName { "." SDOName } "." DAName { "." BDAName }`
  with the Functional Constraint (FC) not embedded in this dot-path at the ACSI/application level at all — it is a separate attribute/qualifier of the DA (see FC section below), not part of the human-readable path. The "[ST]"/"[FC]" bracket style seen in some documentation and tooling appears to be a tutorial/tool convention for disambiguating which functional-constraint "view" of a DA is meant, rather than a literal character sequence defined by the base object-reference grammar in 7-2/7-1.
- The `/` always separates LD from LN; the `.` always separates each subsequent level (LN→DO→SDO→DA→BDA). This is consistent across every source found (vendor docs, OpenSCD/LF Energy wiki, Beckhoff API).

### Gaps
- Could not retrieve the literal BNF/EBNF production for `ObjectReference` as published in IEC 61850-7-2 (the clause defining `FunctionalConstraint`-qualified references); the standard text itself is paywalled and not indexed by general web search. This should be treated as unverified against the primary source.
- Could not confirm whether IEC 61850-7-2 defines a distinct "DataObjectReference" vs. "DataAttributeReference" ACSI type name, or a single unified `ObjectReference` type used for both — none of the secondary sources quoted the exact clause/type names.

---

## What is an FCDA as used inside a `<DataSet>` in SCL, and how do its attributes map to the full object reference?

### Takeaway
An FCDA (Functional Constrained Data Attribute) is an SCL `<FCDA>` element nested inside a `<DataSet>` that names one dataset member via the attributes `ldInst`, `prefix`, `lnClass`, `lnInst`, `doName`, `daName`, and `fc`; concatenating these per the rules above (ldInst → LD; prefix+lnClass+lnInst → LN; doName (with dotted sub-DOs) → DO path; daName (with dotted sub-BDAs) → DA path; fc → the functional constraint tag) yields the full addressable reference, and omitting `daName` turns the same element into an "FCD" that designates a whole constrained data object rather than one attribute.

### Cited Findings
- "If the FCDA element attribute daName is omitted, an FCD is specified. If the FCDA element attribute daName is included, an FCDA is specified." — both reuse the same `<FCDA>` XML element/tag in SCL — [GE B30 manual, IEC 61850 communication guide](https://www.manualslib.com/manual/1282233/Ge-B30.html?page=244)
- A concrete worked `<ExtRef>`/FCDA-style attribute set from a UCA iUG (standards working group) issue thread, as used in a GE UR device guide: `iedName="Fdr1" ldInst="Meter" prefix="ACsrc" lnClass="MMXU" lnInst="1" doName="TotW" daName="mag.f" fc="MX"`, which the same source says maps on the wire (MMS item-id) to `Fdr1Meter/ACsrcMMXU1$MX$TotW$mag$f` — [redmine.ucaiug.org issue tracker via search digest](https://redmine.ucaiug.org/issues/6633) (note: direct fetch of this URL returned HTTP 403; content below is as summarized by the search engine's indexed snippet, so treat the exact attribute values as a probable-but-not-directly-verified quote)
- `doName` was historically optional in the SCL schema but the IEC 61850 Technical Program Working Group (TPWG) recommended making it mandatory; "Specified in 6 Ed2.1" — an SEL conformance note separately confirms "doName now mandatory in FCDA element" in current tooling expectations — [UCAIug Redmine search digest](https://redmine.ucaiug.org/issues/584)
- Dataset-member identity (which LN a member belongs to) is carried by `lnClass` + `lnInst` (+ optional `prefix`), not by `doName` — a UCAIug Redmine issue (#6633) was raised specifically because an LN instance/LDevice combination was missing from an example, confirming these attributes (not doName) are what the schema requires to locate the LN — [UCAIug Redmine #6633 digest](https://redmine.ucaiug.org/issues/6633)
- A GE communications guide gives the dataset-member reference construction order explicitly as: `ldInst` , `LN name` (itself prefix+class+inst), `fc`, `doName`, `daName`, i.e. `ldInst.LNName.fc.doName.daName`, joined by dots in that vendor's documentation style — [GE B30 manual](https://www.manualslib.com/manual/1282233/Ge-B30.html?page=244)
- SCL's `DataSet` groups an ordered list of `FCDA` (and/or `FCD`) elements; an academic paper's figure (SG-ML) shows FCDA fields including `ldInst`, `lnClass`, `doName`, `daName`, and `fc` as the key identifying fields in the SCL XML — [SG-ML: Smart Grid Cyber Range Modelling Language, arXiv](https://arxiv.org/pdf/2509.10568)

### Inferences
- The mapping rule from SCL `<FCDA>` attributes to the full object-reference string is:
  `LD = ldInst (possibly combined with IED name per the SCT/LD-naming mode, see next section)`
  `LN = prefix + lnClass + lnInst`
  `DO-path = doName` (itself possibly dot-separated for nested SDOs, e.g. `PhV.phsA`)
  `DA-path = daName` (itself possibly dot-separated for nested BDAs, e.g. `mag.f`)
  `Reference = LD "/" LN "." DO-path ["." DA-path]`, with `fc` carried alongside as metadata (used explicitly in the MMS wire-level item-id, and implicitly recoverable from the DOType/DA definition even when not written in the human path).
- An `FCD` (no `daName`) therefore designates an entire functionally-constrained data object (all attributes under that FC), while an `FCDA` (with `daName`) pins down one specific (possibly nested) attribute.

### Gaps
- Could not directly fetch the UCAIug Redmine #6633 page (HTTP 403); the ExtRef attribute example and its MMS-mapped string are reported here only via the search engine's own digest/summary of that page, not a verified direct quote. Flagging this as a lower-confidence citation pending primary verification.
- Could not locate the literal IEC 61850-6 Table 22/23 text (FCDA attribute definitions) — only secondary paraphrases of what those tables are understood to require.

---

## How is the "LD Name" actually formed in practice, and what is the "LN Name"?

### Takeaway
In the default/common convention, the LD Name = IED Name concatenated directly with the LDevice `inst` attribute with **no separator character** (e.g., IED name `MA2C03` + LDevice `Relay` → `MA2C03Relay`); IEC 61850-6 Edition 2 additionally allows a system integrator to assign an explicit, independent LD Name (via the LDevice's `ldName` attribute) that replaces this concatenation, as long as it stays unique in the system. The LN Name = optional `prefix` + mandatory 4-letter `lnClass` + mandatory `inst` number (e.g., `ACsrc` + `MMXU` + `1` → `ACsrcMMXU1`), with `LLN0` being the one mandatory logical-node-zero instance every LD must contain.

### Cited Findings
- "A logical device name is created from the IED name and the LD instance name declared in the SCL file from the IED manufacturer; since Edition 2 of IEC 61850-6, the system integrator can choose a logical device name that replaces the concatenation of IED name and vendor-defined LD instance name" — [industry digest of vendor/pacw.org IEC 61850 update article](https://www.pacw.org/iec-61850-update-why-do-top-down-engineering)
- Concrete concatenation example from a libiec61850 library commit: IED name `IED1` + LDevice instance `WD1` (device instance "WD") → resulting LD name `IED1WD` — i.e., straight string concatenation, no separator — [git.0l.de libiec61850 commit diff](https://git.0l.de/stv0g/libiec61850/commit/99c0c8bc75a3189ca11bfa9c5a487c0273541e53.diff)
- Directly-observed API example (not merely documentation prose) from Beckhoff TwinCAT: IED named `MA2C03` with an LDevice whose instance yields the full LD name `MA2C03Relay` (i.e., `MA2C03` + `Relay` concatenated with no separator) — confirmed via the tool's own `GetObjectReference()` output — [Beckhoff infosys](https://infosys.beckhoff.com/content/1033/tf6510_tc3_iec61850/5662798219.html)
- "The logical node names are constructed from three different parts: LN prefix, LN class and LN instance number" — the class name comes from the fixed vocabulary in IEC 61850-7-4 — [tatsoft.com IEC 61850 PDF](https://tatsoft.com/wp-content/uploads/2021/01/IEC61850.pdf)
- "Logical devices are required to have one logical node implementing logical node LLN0" — [GE B30 manual digest](https://www.manualslib.com/manual/1282233/Ge-B30.html?page=243)
- A GE manual states LN names are "formed from the four-character logical node class name ... a prefix ... prefixed by the IED name," with the worked example `ACsrcMMXU1` for "AC source 1" (prefix `ACsrc` + class `MMXU` + instance `1`) — [GE B30 manual digest via search](https://www.manualslib.com/manual/1282233/Ge-B30.html?page=243)
- "Upper/lower case is critically significant in many 61850 names" — i.e., object/name matching is case-sensitive in practice per vendor documentation — [GE manual digest](https://www.manualslib.com/manual/1282233/Ge-B30.html?page=243)

### Inferences
- From the SCL side, this maps as: `IED/@name` + `LDevice/@inst` → default LD Name (string concatenation, no delimiter), UNLESS `LDevice/@ldName` (Ed.2 feature) is present, in which case that explicit value is used verbatim as the LD Name instead.
- `LN0/@lnClass` is always `"LLN0"` for the mandatory logical-node-zero; ordinary `<LN>` elements carry `lnClass`, `inst`, and optional `prefix` attributes that are concatenated in the fixed order `prefix + lnClass + inst` to form the LN Name used in the object reference.

### Gaps
- Could not verify the exact XSD attribute name for the Ed.2 "explicit LD name" override (whether it is `ldName` on `<LDevice>` or a separate construct) against the primary IEC 61850-6 text; this is inferred from a secondary paraphrase only (pacw.org article), not a schema excerpt.

---

## What is the role of the Functional Constraint (FC), and how/where is it represented in SCL?

### Takeaway
The Functional Constraint (FC) is a classification tag (ST, MX, CO, SP, CF, DC, EX, SG, SE, etc.) that groups a logical node's data attributes by the kind of service/access they support (status, measurement, control, setting, etc.); in SCL it is written explicitly as the `fc` attribute on each `<FCDA>` element inside a `<DataSet>`, and implicitly/normatively on each `<DA>` (and `<BDA>`) element inside the `DataTypeTemplates/DOType` (and `DAType`) definitions, since the FC is actually a fixed property of the data attribute's definition in the underlying Common Data Class (IEC 61850-7-3), not something assigned freely per dataset.
Because of the SCL FC Enum Instance tagging confusion noted below, FC should be read as attached to the DA's class definition first, and the SCL `fc` attribute on FCDA is a convenience re-statement/confirmation of that same value for the dataset-membership context (and, per one standards-body dispute, the FC of an attribute within a structured DO is actually determined by the DA-level elements of the underlying CDC, not by the containing DO/SDO structure).

### Cited Findings
- "The function defined by the LN will contain several objects that are distributed in categories defined as FC — Functional Constraints" — [tatsoft.com IEC 61850 overview PDF](https://tatsoft.com/wp-content/uploads/2021/01/IEC61850.pdf)
- Example FC usage in a vendor dataset-member/MMS mapping: `fc="MX"` in SCL attributes maps to the `$MX$` segment of the MMS item-id `Fdr1Meter/ACsrcMMXU1$MX$TotW$mag$f` — [UCAIug Redmine #6633 digest](https://redmine.ucaiug.org/issues/6633)
- "fc: The functional constraint is defined by the DA elements of the underlying common data class, not by the containing structure" — raised in a standards dispute about whether `phsA`-type sub-objects under a WYE/CMV structure get their FC from the WYE wrapper or from the CMV's own DA elements; resolution favored the latter (DA-level definition) — [UCAIug Redmine issue digest](https://redmine.ucaiug.org/issues/6633)
- "phsA ... which are Data Object, not Attributes — of class CMV. The FC is defined by DA elements of CMV, not by elements of WYE." — confirms FC is a property that travels with the leaf/attribute-bearing CDC (e.g., CMV), inherited down through SDO nesting rather than re-declared at each nesting level — [UCAIug Redmine digest](https://redmine.ucaiug.org/issues/6633)
- GE's dataset member reference order places `fc` between the LN name and `doName`/`daName`: `ldInst.LNName.fc.doName.daName` — [GE B30 manual digest](https://www.manualslib.com/manual/1282233/Ge-B30.html?page=244)
- The MMS mapping (IEC 61850-8-1) places FC as a literal `$`-delimited segment in the server item-id: `LDName/LNName$FC$DOName$DAName...`, e.g. `XCBR1$ST$Mod$stVal` and `Fdr1Meter/ACsrcMMXU1$MX$TotW$mag$f` — [Elipse driver docs](https://docs.elipse.com.br/documents/en-us/driver/iec61850srv/latest/iec61850srv_about_iec_61850.html); [GE B30 manual](https://www.manualslib.com/manual/1282233/Ge-B30.html?page=244)

### Inferences
- In SCL, `fc` appears explicitly on `<FCDA>` (dataset membership) because a dataset must pin down exactly which FC-view of a DA is being reported/sent (relevant when a DA name could conceivably exist under more than one FC-context, although in practice each DA in a given CDC normally has one fixed FC).
- At rest in `DataTypeTemplates`, FC is not a separate SCL attribute of `<DA>`/`<BDA>` in the way `fc` appears on `<FCDA>` — rather, FC is implied by which Common Data Class (CDC, e.g., SPS = ST, MV = MX, SPC = CO/ST, etc., per IEC 61850-7-3) the owning DOType conceptually instantiates, and by convention/vendor practice the DA's role (and therefore FC) is fixed by the standard CDC definition, which SCL tooling must know independent of the file (i.e., an external CDC→FC lookup table derived from IEC 61850-7-3 is required to resolve FC purely from a DOType/DA without also consulting the FCDA's own `fc` attribute).
- For an automated reference-resolution algorithm: the safest FC source is the FCDA's own `fc` attribute when resolving dataset/GOOSE/report members; when resolving arbitrary DA paths outside a dataset (e.g., for direct MMS reads), FC must be derived from the CDC definition of the DO's type (SPS→ST, MV family→MX, controllable DOs→CO+ST, settings→SP/SG/SE, config→CF, description→DC, extended→EX), per IEC 61850-7-3.

### Gaps
- Could not find a primary-source confirmation (direct 7-3 or 6 text) of the full CDC→FC assignment table; only the ST/MX/CO/SP/CF/DC/EX/SG/SE abbreviation list as given in the assignment's own framing was corroborated indirectly, not exhaustively sourced per-CDC.
- Could not confirm whether SCL's `<DA>`/`<BDA>` elements inside `DOType`/`DAType` ever carry an explicit `fc` XML attribute in the schema (as opposed to FC being purely inferable from the CDC) — none of the fetched sources showed a DOType/DA XML snippet with an `fc=` attribute visible.

---

## How are nested/structured data objects (SDO) and nested basic data attributes (BDA) addressed, and how does this appear in SCL's type chains?

### Takeaway
Structured addressing uses the same dot-separated path convention recursively: a Data Object can contain sub-Data-Objects (SDO) that themselves resolve to another DOType (e.g., `PhV.phsA` where `PhV` is a WYE-typed DO and `phsA` is an SDO of CDC type CMV), and a Data Attribute can contain sub-Basic-Data-Attributes (BDA) that resolve to another DAType (e.g., `cVal.mag.f` or `mag.f` under a CMV/AnalogueValue structure). In SCL this is modeled in `DataTypeTemplates` as a type-resolution chain: `DOType` entries list `<DO>`/`<SDO>` children whose `type` attribute points to another `DOType` id (for sub-DOs) or terminate in `<DA>` children whose `type` attribute points to a `DAType` id (for structured attributes) or a `bType` (for basic types); `DAType` entries in turn list `<BDA>` children whose `bType` is either a basic type or `"Struct"` (in which case `BDA/@type` points to yet another `DAType` id), making the whole chain recursively resolvable. Instance-side (in the `<IED>` section), the same nesting is mirrored by `<DOI>` → `<SDI>` → `<DAI>` elements.

### Cited Findings
- "DOs consist of attributes (DA) or of elements of already defined DO types (SDO)" — i.e., a `DOType` is built from a mix of `<DA>` (attribute) and `<SDO>` (sub-object, referencing another `DOType`) children — [LF Energy / OpenSCD wiki digest](https://lf-energy.atlassian.net/wiki/x/TwAgCQ)
- Worked example: a WYE-typed DO's three phase sub-objects are SDO entries that each point to a CMV-typed `DOType` — "the second example is more complex as it consists of another CDC (CMV) and structure data attributes" — [LF Energy wiki digest](https://lf-energy.atlassian.net/wiki/x/TwAgCQ)
- "A DA can be a basic type, an enumeration, or a structure. The DAType is built from BDA elements... a BDA's bType is either a basic type or 'Struct', in which case its type attribute names another DAType" — confirming the recursive DAType→BDA→DAType chain — [LF Energy wiki digest](https://lf-energy.atlassian.net/wiki/x/TwAgCQ)
- "In the IED section, instantiated data appears as DOI, SDI and DAI elements, which mirror the type hierarchy" — the instance-side (actual IED configuration values/overrides) mirrors the abstract `DataTypeTemplates` type hierarchy one-for-one — [LF Energy wiki digest](https://lf-energy.atlassian.net/wiki/x/TwAgCQ)
- "Tooling resolves a type by following the `type` attributes from a DO or SDO up through DOType/DAType ids, then to the LNodeType" — confirms the resolution direction: `LNodeType` → (its `<DO>` entries' `type` attrs) → `DOType` → (its `<SDO>`/`<DA>` entries' `type`/`bType` attrs) → further `DOType`/`DAType` → ... — [LF Energy wiki digest](https://lf-energy.atlassian.net/wiki/x/TwAgCQ)
- "Since Edition 2, CDC cannot be extended" — the set of Common Data Classes (SPS, WYE, CMV, MV, etc., defined in IEC 61850-7-3) is closed; custom structures are only composed from these fixed CDCs, not invented ad hoc — [LF Energy wiki digest](https://lf-energy.atlassian.net/wiki/x/TwAgCQ)
- A disputed-but-illustrative example path for nested addressing: `AmpMMXU1.A.phsA.cVal.mag.f` (LN `AmpMMXU1` → DO `A` (measured amps, CDC=WYE) → SDO `phsA` (CDC=CMV) → DA `cVal` (structured attribute, AnalogueValue) → BDA `mag` (structured, "Analogue") → BDA `f` (basic FLOAT32)) — [LF Energy wiki, earlier example](https://lf-energy.atlassian.net/wiki/spaces/SHP/pages/154009785)

### Inferences
- The dot-separated object-reference path directly mirrors the DOType/SDO and DAType/BDA nesting depth: every `.` after the DO name corresponds either to one more hop down an SDO chain (while still inside DO-type territory, i.e. CDC-to-CDC) or, once attribute-level is reached, one more hop down a BDA chain (struct-to-struct inside a DAType), e.g. `A` (DO) `.phsA` (SDO) `.cVal` (DA, structured) `.mag` (BDA, structured) `.f` (BDA, basic) — five path segments corresponding to five resolution hops through `LNodeType→DOType(WYE)→DOType(CMV)→DAType(AnalogueValue? / Vector)→DAType(Analogue)→basic FLOAT32`.
- For an automated resolver, this means: given a full object reference string, one cannot know purely from dot-counting whether a given segment is an SDO (DO-to-DO hop) or a BDA (DA-to-DA hop) — this requires walking the actual `DataTypeTemplates` type chain (starting from the LN's `LNodeType`, then its `<DO>` entries, then recursively through `DOType`/`DAType` definitions) to classify each segment correctly, rather than relying on syntax alone.

### Gaps
- Could not obtain a primary IEC 61850-7-3/61850-6 citation distinguishing the exact schema element names/attributes for `<SDO>` vs. plain `<DO>` vs. `<DA>` inside `<DOType>` (e.g., whether SCL literally uses a tag named `<SDO>` versus simply another `<DA>` with a `type` attribute pointing at a DOType) — the LF Energy wiki source uses "SDO" as a descriptive/conceptual term, and it was not independently cross-checked against a raw SCL XSD or schema excerpt.

---

## What length/character constraints exist on these names per the standard?

### Takeaway
Vendor documentation (echoing IEC 61850-6/-7-2 naming rules, though not independently verified against the primary standard text) consistently reports: IED Name 1–64 "VisibleString" characters; the combined LD Name (IED name + LDevice inst, or explicit `ldName`) capped at 64 characters total (forcing IED names to be shorter, e.g. ≤58 chars, to leave room for the LDevice instance suffix); LN prefix capped at 11 characters (one source: Ed.2 limits are "64 characters for the LD name and 11 characters for the LN prefix"); names must start with a letter and may contain letters, digits, and underscore; and name matching/comparison is case-sensitive.

### Cited Findings
- "64 characters for the LD name and 11 characters for the LN prefix" (stated as the Edition 2 length limits) — [industry digest, pacw.org IEC 61850 update article](https://www.pacw.org/iec-61850-update-why-do-top-down-engineering)
- "the IED name must be capped at 58 characters to stay within 64" (because LDName = IEDName + LDInst must fit in 64 total) — [GE L60 manual digest](https://www.manualslib.com/manual/1257229/Ge-L60.html?page=215)
- "A GE UR manual gives the IED name range as 1 to 64 VisibleString characters" — [GE M60 manual digest](https://www.manualslib.com/manual/1336924/Ge-M60.html?page=172)
- "the same 64-character ceiling and requires the first character to be a letter" — [GE 350 manual digest](https://www.manualslib.com/manual/1281367/Ge-350.html?page=124)
- "valid characters are letters, digits, and underscore" — [GE manual digests, cross-referenced](https://www.manualslib.com/manual/1281367/Ge-350.html?page=124)
- "a logical node name totals 11 characters, made up of a five- or six-character prefix plus the node name" (i.e., prefix ~5-6 chars + 4-char lnClass + 1-digit inst ≈ 11 total in that vendor's constrained implementation) — [GE N60 manual digest, pointing to IEC 61850-6 and -7-2](https://www.manualslib.com/manual/1363809/Ge-N60.html?page=484)
- "Upper/lower case is critically significant in many 61850 names" — [GE B30 manual digest](https://www.manualslib.com/manual/1282233/Ge-B30.html?page=243)
- The normative source for exact length/character rules is the SCL XSD itself, which IEC states takes precedence over the PDF text in case of conflict ("In case of any differences between the downloadable code component and the IEC PDF published content, the downloadable code component is the valid one") — [VDE-Verlag IEC 61850-6 Ed2.2 info page](https://vde-verlag.de/iec-normen/preview-pdf/info_iec61850-6%7Bed2.2%7Den.pdf)

### Inferences
- The 64-character LD-name ceiling is the binding constraint that in practice limits IED name length (since LDName = IEDName + LDInst with no separator); tooling and automated resolvers should treat the concatenated LD name's total length, not the IED name alone, as the hard limit to validate against.
- LN name length constraints (≈11 characters total for prefix, observed in at least one vendor's stricter profile) should be treated as a vendor-level/profile-level constraint layered on top of whatever the base standard allows, since the cited figure comes from a vendor implementation note referencing (but not quoting) IEC 61850-6/-7-2.

### Gaps
- Could not retrieve or verify the literal SCL XSD regex pattern (e.g., a `tAnyName`-style simple-type pattern restricting to `[A-Za-z][A-Za-z0-9_]*`) — web search did not surface the raw XSD content; this is the single most important gap for building an automated validator, and the recommendation is to obtain the actual IEC 61850-6 SCL.xsd code component directly from the IEC webstore (noted as the authoritative artifact) rather than relying on any further secondary paraphrase.
- Could not confirm the exact maximum lengths defined in the primary standard for `doName`/`daName` path segments or total object-reference string length (if any) — no source addressed this directly.

---

## How does GOOSE/SV addressing differ from client–server (MMS) addressing?

### Takeaway
GOOSE and Sampled Values (SV) messages carry only the raw values of a DataSet's members, in the DataSet's configured order, with no names, no indexes, and no embedded object-reference strings on the wire; the receiving IED must already hold (via prior SCL/CID engineering) the same DataSet definition to know which position in the payload corresponds to which FCDA. MMS client–server access (reads/writes/reports), by contrast, is genuinely name/reference based: the client addresses data using the full hierarchical object reference (mapped at the wire level to an MMS item-id using `$` as the level separator, including an explicit FC segment), resolved live against the server's named variable/domain structure.

### Cited Findings
- "The semantic is determined by the order of the corresponding DataSet" — for GOOSE and Sampled Values, values are carried positionally with no names or indices in the message itself — [NettedAutomation blog, "Bandwidth usage: IEC 61850 object..."](https://blog.nettedautomation.com/2014/03/bandwidth-usage-iec-61850-object.html)
- A blog commenter (Rod Hughes, identified in-thread as knowledgeable on the topic) adds: "the DataSet does not carry the prefix/suffix, the Logical Node name, or the DA or DO name" on the wire — the full names exist only so humans and engineering tools can understand the configuration, not for runtime transmission — [NettedAutomation blog comments](https://blog.nettedautomation.com/2014/03/bandwidth-usage-iec-61850-object.html?m=1)
- GOOSE messages additionally carry a GOOSE identifier (e.g., `GoID`/AppID-level identification) so the subscriber knows which configured DataSet/subscription the positional values belong to, per the same blog thread — [NettedAutomation blog comments](https://blog.nettedautomation.com/2014/03/bandwidth-usage-iec-61850-object.html?m=1)
- Report messages (a third, related but distinct mechanism, client–server-based but using a DataSet like GOOSE) include an inclusion bitstring that marks which DataSet position changed, so the client still needs the pre-configured DataSet definition to interpret which FCDA changed, even though reports are delivered over the client–server (MMS) association — [NettedAutomation blog](https://blog.nettedautomation.com/2014/03/bandwidth-usage-iec-61850-object.html)
- For genuine ad hoc MMS client reads/writes (not report/GOOSE/SV dataset-based exchange), the full object reference is used, mapped to an MMS item-id of the form `LDName/LNName$FC$DOName$DAName...`, e.g., `Fdr1Meter/ACsrcMMXU1$MX$TotW$mag$f` and `XCBR1$ST$Mod$stVal` — [GE B30 manual](https://www.manualslib.com/manual/1282233/Ge-B30.html?page=244); [Elipse driver docs](https://docs.elipse.com.br/documents/en-us/driver/iec61850srv/latest/iec61850srv_about_iec_61850.html)
- "Datapoints in exchanged data must be data objects and not attributes, otherwise they won't work [for GOOSE/report subscription]; specific data attributes are chosen in dataset configuration" — reinforces that for dataset-based exchange (GOOSE/SV/Report), the addressable unit is fixed at DataSet-engineering time via the FCDA list, not resolved dynamically per-message — [LF Energy wiki digest](https://wiki.lfenergy.org/x/yWHGAg)

### Inferences
- For an automated reference-resolution algorithm, this means two very different resolution modes are needed:
  1. **MMS/client–server mode:** resolve a live object-reference string (with explicit or inferred FC) directly against the server's/IED's `DataTypeTemplates`-derived model, on demand, per request.
  2. **GOOSE/SV/Report mode:** resolution must happen once, at engineering time, by walking the referenced `<DataSet>`'s ordered `<FCDA>` list and building a fixed position→object-reference lookup table; at runtime (or when simulating runtime behavior from a captured frame), the only available information is the DataSet identity and member position, so the mapping back to a human-readable reference requires the original SCL/CID DataSet definition — it cannot be recovered from the GOOSE/SV frame alone.

### Gaps
- Could not find a primary-source (standard-text) description of the exact GOOSE PDU structure confirming "no names in the payload" beyond the NettedAutomation blog's informal description; this is corroborated by a credible industry blog and commenter but not directly quoted from IEC 61850-8-1/-9-2.

---

## Worked examples of constructing a full object reference string from SCL fragments

### Takeaway
Three concrete, source-grounded examples below show the reference-construction process end to end: (1) a directly-observed API-level example (Beckhoff/TwinCAT) demonstrating IED+LDevice concatenation and the `/`/`.` separator rules; (2) a vendor-documented FCDA→MMS mapping example showing how SCL `<FCDA>` attributes (including `fc`) become a wire-level item-id; (3) a nested-structure example showing SDO/BDA dot-path construction for a measured-value CDC.

### Cited Findings

**Example 1 — IED/LD/LN/DO/DA concatenation (Beckhoff TwinCAT IEC 61850 API)**
SCL-equivalent fragment: IED `name="MA2C03"`, containing an `<LDevice inst="Relay">`, containing `<LN0 lnClass="LLN0">` with a `<DO name="Mod">` whose type resolves to a DOType containing `<DA name="stVal">`.
Resulting reference strings, as literally returned by the tool's `GetObjectReference()` calls:
- IED → `MA2C03`
- Logical device → `MA2C03Relay` (IED name `MA2C03` + LDevice inst `Relay`, concatenated with no separator)
- LN → `MA2C03Relay/LLN0`
- DO → `MA2C03Relay/LLN0.Mod`
- DA → `MA2C03Relay/LLN0.Mod.stVal`
— [Beckhoff infosys TF6510 TC3 IEC61850 documentation](https://infosys.beckhoff.com/content/1033/tf6510_tc3_iec61850/5662798219.html)

**Example 2 — SCL FCDA attributes → MMS item-id (vendor-documented, GE/UCAIug)**
SCL `<FCDA>`-equivalent attribute set: `iedName="Fdr1" ldInst="Meter" prefix="ACsrc" lnClass="MMXU" lnInst="1" doName="TotW" daName="mag.f" fc="MX"`.
Construction: LD = `Fdr1` + `Meter` = `Fdr1Meter`; LN = `ACsrc` + `MMXU` + `1` = `ACsrcMMXU1`; DO/DA path = `TotW.mag.f` (DO `TotW`, nested BDA path `mag.f`); FC = `MX`.
Resulting MMS wire-level item-id (per IEC 61850-8-1 mapping, `$`-delimited): `Fdr1Meter/ACsrcMMXU1$MX$TotW$mag$f`
— [UCAIug Redmine issue #6633, as summarized in search digest](https://redmine.ucaiug.org/issues/6633) (direct page fetch returned HTTP 403; treat exact attribute values as moderate-confidence, sourced via search-engine digest of that page rather than a verified direct quote) and corroborated independently by [GE B30 communications manual](https://www.manualslib.com/manual/1282233/Ge-B30.html?page=244), which documents the same `ldInst.LNName.fc.doName.daName` construction order for dataset members.

**Example 3 — Nested SDO/BDA addressing (measured current, WYE/CMV structure)**
Reference: `AmpMMXU1.A.phsA.cVal.mag.f`
Construction, hop by hop:
- `AmpMMXU1` = LN (prefix `Amp` + lnClass `MMXU` + inst `1`)
- `.A` = Data Object of CDC type WYE (three-phase wye-connected measurement group)
- `.phsA` = SDO (sub-data-object) of CDC type CMV (complex measured value), nested inside the WYE DOType
- `.cVal` = DA of structured type (AnalogueValue-like structure) inside the CMV DOType
- `.mag` = BDA (structured) inside that DAType, representing the magnitude sub-structure
- `.f` = BDA (basic FLOAT32) — the final leaf value
— [LF Energy / OpenSCD wiki](https://lf-energy.atlassian.net/wiki/spaces/SHP/pages/154009785)

### Inferences
- All three examples confirm the same universal construction rule: `(IEDName ⊕ LDInst) "/" (Prefix ⊕ LNClass ⊕ LNInst) "." DOName{"."SDOName} {"." DAName{"."BDAName}}`, where `⊕` denotes plain string concatenation (no separator) and FC travels alongside as metadata that is written inline only at the MMS wire-mapping stage (as a `$FC$` segment), not inside the dot-path itself.
- An automated resolver built against SCL should: (a) build LD names by concatenating `IED/@name` with `LDevice/@inst` (or substituting `LDevice/@ldName` if present per Ed.2); (b) build LN names by concatenating `@prefix` (if any) + `@lnClass` + `@inst`; (c) resolve DO/DA paths by walking `DataTypeTemplates` from the LN's `@lnType` through `LNodeType → DOType → (DOType|DAType)...` chains, concatenating each level's `name` attribute with `.`; (d) attach FC either from the governing `<FCDA>/@fc` (when resolving dataset members) or from the CDC-implied FC of the terminal DA's type (when resolving a bare path outside a dataset context).

### Gaps
- Could not obtain a reference example directly copy-pasted from the IEC 61850 standard text itself (e.g., an official Annex example such as a literal "`IED1LD0/PTOC1.Op.general[ST]`"-style string) — targeted searches for this exact style of example and for PTOC/XCBR examples did not surface a primary-source document containing it; all three worked examples above are vendor/community-documented rather than lifted verbatim from the IEC standard's own text. This is the main gap: a report author wanting to cite the IEC standard's own worked examples (rather than vendor/community restatements of the same rules) will need direct access to IEC 61850-6, -7-1, -7-2, -7-3, or -7-4 (paywalled, e.g. via webstore.iec.ch or standards.iteh.ai), none of which were fetchable as full text through available tools.
