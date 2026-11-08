# Plan: IEC 61850 SCL parsing/validation/structure research notes

## Status
Plan mode is active, so I have not written the deliverable file yet. Research (read-only web search/fetch) is complete — roughly 17 tool calls across WebSearch and WebFetch, covering parsing, XSD validation, semantic/consistency checks, conformance rules, known validators, SCL containment hierarchy, type/instance separation, object-reference construction, Communication-section cross-references, and DataSet/FCDA/control-block/ExtRef relationships.

## What I will do once you confirm (exit plan mode)
Write the draft below verbatim (in the exact `# Title / ## Key Question / ### Takeaway / ### Cited Findings / ### Inferences / ### Gaps` format required by the research-notes convention) to:

`D:\Trivium-Inhouse\SCD-POC\research_notes\IEC 61850 SCL formats and tools\parsing_validation_structure.md`

No other files or systems will be touched.

## Notes on source quality
Primary/standard-body sources (IEC/BSI/VDE catalog pages, UCA iUG redmine tracker, CoMPAS/OpenSCD project wiki and GitHub) were preferred. Several points rely on vendor manuals (GE, Beckhoff), blog posts (nettedautomation, digitalsubstation), or a secondary summary (DeepWiki for libiec61850) because primary text (the IEC 61850-6 PDF itself, libiec61850 source tree) was not directly fetchable in this session (GitHub/DeepWiki fetches returned 404/429). These are flagged inline as lower-confidence. I was not able to browse the libiec61850 GitHub source tree directly (no `gh`/browser access used in research mode), so parser-internals claims for that library are from secondary summaries only — flagged as a gap.

---

## DRAFT DELIVERABLE (to be saved to the research_notes file verbatim)

# IEC 61850 SCL formats and tools — parsing, validation, structure

## Parsing: DOM vs streaming, namespace handling

### Takeaway
Production SCL tools overwhelmingly use DOM-style (or DOM-equivalent, e.g. JAXB-bound) parsing because SCL's cross-referential structure (lnType → LNodeType → DOType → DAType, ConnectedAP → IED, datSet → DataSet) requires random access across the whole document; pure streaming/SAX is used only as a pre-filtering or chunked-loading step for very large files, not as the primary model-building strategy.

### Cited Findings
- The CoMPAS SCT (SCL Consistency Tool) documentation states plainly that for a large SCL file "it is not a good idea to load the whole file in memory," and recommends extracting a minimal valid file (Header + the IED of interest + DataTypeTemplate) to work on; it also notes that full XSD validation "needs the entire file content," so chunked/streaming approaches (it mentions JAXB can process XML in chunks) are used only for non-validating work, with validation falling back to a reduced copy — [compas-sct docs](https://com-pas.github.io/compas-sct/compas-sct.html).
- A University of Vaasa thesis, "Improving the Scalability and Performance of an IEC 61850-6 SCL Workflow," reports a redesign using a dictionary trie plus XSD-generated (JAXB-style) classes, claiming parsing of sample SCL files became 369.1x faster after the redesign — [osuva.uwasa.fi record](https://osuva.uwasa.fi/handle/11111/20947) (full text could not be fetched in this session — see Gaps).
- OpenSCD (browser-based SCL editor) treats "a project" as synonymous with an SCL file and keeps all project data as SCL/XML validated against the schema, implying an in-memory DOM-like document model is held for editing — [OpenSCD / LF Energy description](https://lfenergy.org/?p=9187).
- Triangle MicroWorks sells a commercial "IEC 61850 Source Code Library" whose merged schema supports SCL files for Edition 1, Edition 2 and Edition 2.1 — implying commercial libraries maintain their own internal schema/version abstraction layer rather than relying on raw per-edition XSDs — [Triangle MicroWorks](https://files.trianglemicroworks.com/products/source-code-libraries/iec-61850-scl-pages/benefits).
- libiec61850 (mz-automation) includes a "Static Model Generator" (named in third-party documentation as `StaticModelGenerator.java`) that parses an SCL/ICD file and generates C code defining the IED's data model structure at compile time, i.e., it converts the DOM-parsed SCL model into a static, indexed in-memory structure rather than re-walking XML at runtime — [DeepWiki summary of mz-automation/libiec61850](https://deepwiki.com/mz-automation/libiec61850/5-data-model) (secondary/AI-generated summary, not the primary source — see Gaps).

### Inferences
- The pattern across tools (CoMPAS SCT, OpenSCD, Triangle MicroWorks, libiec61850) is: parse once into an in-memory object graph (DOM or a typed binding such as JAXB), then build or cache cross-reference indexes (id→LNodeType, id→DOType, iedName→IED, etc.) so that reference resolution is O(1) lookups rather than repeated tree search. This explains why trie/dictionary-based indexing (as in the Vaasa thesis) gives large speedups: the bottleneck is reference lookup, not raw XML tokenizing.
- Default-namespace handling is largely implicit in these tools: because SCL documents normally declare a single default namespace (the SCL namespace) and only `Private` content carries vendor namespaces, most tools do not need full namespace-aware XPath; they parse the default-namespace elements directly and treat anything under `Private` (or any element bearing an unrecognized namespace) as opaque.

### Gaps
- No primary source was retrievable that documents SAX/streaming SCL parsers used in production (the Vaasa thesis full text returned an access-denied/Anubis bot-block page; the libiec61850 GitHub source tree was not directly browsed in this read-only research session).
- No source confirmed whether any mainstream commercial SCT/ICT tool uses genuine streaming (single-pass, non-DOM) parsing for the full load-and-validate pipeline as opposed to just an initial "read header/IED list" prefilter.

## Parsing: handling of the `<Private>` element

### Takeaway
`<Private>` is a standard, schema-defined "escape hatch" (any vendor-defined child content plus a mandatory `type` attribute that acts as a namespace/owner discriminator); the universal convention among tools — stated explicitly by at least one vendor manual and implied by the CoMPAS extension pattern — is to preserve Private content opaquely and unmodified unless the tool itself is the "owner" of that Private type.

### Cited Findings
- IEC 61850-6 defines the `Private` element and its attributes as part of the SCL schema itself; the current consolidated edition is Edition 2.2 (2024), which includes a dedicated section on extension handling and a worked extension example — [VDE Verlag IEC 61850-6 ed2.2 info page](https://vde-verlag.de/iec-normen/preview-pdf/info_iec61850-6%7Bed2.2%7Den.pdf).
- A GE UR-series IED manual states the convention directly: Private elements are understood only by the tool that inserted them; "Only the owner's tools are allowed to modify a Private element. Other tools are required to preserve Private elements unchanged." — [GE UR Series manual](https://www.manualslib.com/manual/1230075/Ge-Ur-Series.html?page=228).
- The same manual notes that different manufacturers — and even different tools from the same manufacturer — use Private elements for different, non-interoperable purposes.
- The CoMPAS project's documented extension pattern is to define a separate XSD schema for additional elements/attributes and place that content inside a `Private` element carrying a `type` attribute plus a namespaced child element, rather than extending the base SCL schema — [CoMPAS XSD Extensions](https://com-pas.github.io/compas-architecture/technical/XSD_EXTENSIONS.html).

### Inferences
- Because `Private`'s child content is schema-wise `xs:any`/open content, a parser cannot and does not attempt semantic interpretation of unknown `type` values; the correct general-purpose ingestion behavior is: parse and retain the raw XML subtree (including the `type` attribute) for round-tripping, and only decode/interpret it when the tool recognizes the specific `type` string as one it owns.
- This also means `Private` content is a plausible vector for vendor-specific IED configuration (e.g., protection settings) that an SCL-ingestion tool must not silently drop on round-trip, even though it is semantically opaque.

### Gaps
- Did not find the exact XSD attribute list/cardinality for `Private` (e.g., whether `type` is a free-form string vs. enumerated, or how many child elements are permitted) — would need the IEC 61850-6 schema (`SCL.xsd`) text directly, which was not fetched in this session.

## Parsing: handling of large SCD files (performance)

### Takeaway
The documented strategies are (a) avoid loading/validating the full SCD when only part of it is needed — extract a reduced file containing just Header + the IED(s) of interest + DataTypeTemplates — and (b) replace naive repeated tree-walks with indexed/trie-based lookup structures; there is no evidence of a widely adopted true-streaming (SAX-only) SCD ingestion pipeline because full XSD validation requires the whole document in memory/stream regardless.

### Cited Findings
- CoMPAS SCT: "For large SCL file, it is not a good idea to load the whole file in memory" and recommends working against an extracted minimal valid file (Header, the IED, DataTypeTemplate), while noting "validation processes need the entire file content" — [compas-sct docs](https://com-pas.github.io/compas-sct/compas-sct.html).
- The Vaasa thesis abstract reports a 369.1x parsing speed improvement after introducing a dictionary trie and XSD-generated (JAXB) classes for an SCL workflow — [osuva.uwasa.fi](https://osuva.uwasa.fi/handle/11111/20947).
- A CopaData knowledge-base article documents a real-world failure mode: an "IEC61850 server fails to import SCL file with excessive XML tags," i.e., very large/tag-heavy SCD files can exceed a given tool's import capacity — [CopaData KB article](https://selfservice.copadata.com/portal/en/kb/articles/iec61850-server-fails-to-import-scl-file-with-excessive-xml-tags-19-7-2022) (title/topic only; full content not fetched).

### Inferences
- A practical architecture for a new SCL-ingestion tool handling station-level SCDs (tens of MB, many IEDs) is: (1) a lightweight first pass (could be streaming) to index IED names/byte offsets without building full objects, (2) on-demand/lazy full parse of a single IED's subtree plus the shared DataTypeTemplates section, and (3) a separate, explicit "full validate" pass that necessarily loads everything, run only when required (e.g., before import/export) rather than on every read.

### Gaps
- No public source quantifies real file sizes/IED counts at which specific commercial tools start to degrade, beyond the general statement that excessive tag counts can break import in at least one product (CopaData).
- No confirmed description of any tool using a true single-pass SAX validator for XSD + semantic checks together (vs. DOM-based validation).

## Parsing: schema/namespace versioning across editions (2003/A, 2007/B, 2.1 amendments)

### Takeaway
SCL carries its own "edition" information via the fixed XML namespace URI (`http://www.iec.ch/61850/2003/SCL`, unchanged across editions) plus a `version`/`revision`/`release` set of attributes on the `<SCL>` root element (commonly summarized as e.g. "2007B4"); Edition 2 added substantial new SCL constructs (notably `ExtRef`-based input binding, `Services`, enhanced `Private`/extension guidance) that Edition-1-only parsers do not understand, and Edition 2.1 made further clarifications (e.g., to `confRev` and FCDA/dataset reference rules) without changing the namespace URI.
- A blog post on IED Scout notes that an SCL logical device with no explicit namespace value defaults to interpretation as Edition 1 — [nettedautomation blog](https://blog.nettedautomation.com/2016/07/experience-with-omicron-iedscout.html).
- The IEC 61850-7-4 publication table lists Edition 1.0 (2003-05) under the "2003" namespace scheme and Edition 2.0 (2010) under the "2007" scheme, with Amendment 1 designated "2007B" — [BSI standards development project page](https://standardsdevelopment.bsigroup.com/projects/2025-02806).
- A third-party standards catalog entry for IEC 61850-6:2009/AMD1:2018 gives the SCL XML namespace URI as `http://www.iec.ch/61850/2003/SCL`, labeled internally as "Namespace Version 2007, Revision B, Release 4" — i.e. the URI keeps the literal string "2003" permanently while the actual semantic version is tracked by separate version/revision/release attributes, not the URI — [iTeh standards catalog](https://standards.iteh.ai/catalog/standards/iec/79b75107-5dc2-454a-9f11-25844c133dce/iec-61850-6-2009-amd1-2018).
- A UCA iUG (redmine) bug report describes a real interoperability failure: an SCL file declaring version "2007" (without the "A"/"B" revision letter) failed to import because the importing tool specifically expected "2007A"; this was treated as a standard-clarification issue, not a bug in either tool — [UCA iUG issue 450](https://redmine.ucaiug.org/issues/450).
- A 2015 blog post states that conformance testing of that era used "SCL 1.7" for Edition 1 and "SCL.2007B" for Edition 2 — [nettedautomation blog, IEC 61850-6 label](https://blog.nettedautomation.com/search/label/IEC%2061850-6?m=0).
- Commercial libraries (Triangle MicroWorks) advertise a "merged schema" supporting SCL for Edition 1, Edition 2, and Edition 2.1 simultaneously, implying vendors build a superset internal schema/model rather than switching schemas file-by-file — [Triangle MicroWorks SCL page](https://files.trianglemicroworks.com/products/source-code-libraries/iec-61850-scl-pages/benefits).
- Edition-2-specific feature: ExtRef-based "Inputs" binding for GOOSE/SV subscription is an Edition 2 construct; a secondary source (a BHEL tool write-up) states Edition 2 "binds external signals through Inputs tags, and the remote IED must be present in the SCD file" — [Scribd write-up](https://www.scribd.com/document/630104303/writeup) (secondary source, flagged lower confidence).
- Edition 2.1 changes confirmed by a technical article: clarified when `confRev` must increment for Report control blocks (element addition), and restricted when the reserved value 0 may be used for GOOSE/SV/Report blocks with no dataset reference — [digitalsubstation confRev article](https://digitalsubstation.com/article/confrev-61850-goose-sv-en).

### Inferences
- A robust SCL parser should read the `<SCL>` root element's version/revision/release attributes (not just assume a given schema from the namespace URI, since the URI string is frozen at "2003" regardless of actual edition) to decide which semantic rule-set (Edition 1 vs 2 vs 2.1) to apply, and should tolerate files that omit or vary the revision letter (as the "2007" vs "2007A" interoperability bug shows real-world laxness here).
- Because Edition 2 introduces genuinely new elements (`Services`, `ExtRef`/Inputs, expanded `Private`/extension guidance) that are simply absent from the Edition-1 schema, an ingestion tool targeting both editions needs either two schema sets selected by root-attribute sniffing, or a superset internal schema (as commercial vendors do) with edition-gated semantic validation layered on top.

### Gaps
- Could not retrieve the literal attribute names/values as given in the IEC 61850-6 standard text itself (e.g., the exact attribute name(s) used for "version/revision/release" on `<SCL>`) — the above is reconstructed from secondary descriptions (catalog metadata, blog posts) rather than the schema file. A new ingestion tool should confirm the exact attribute names directly from `SCL.xsd`.

## Validation: XSD schema validation — which files, and what on `<SCL>` picks the schema

### Takeaway
IEC 61850-6's normative schema (Annex A) is split across several cooperating XSD files — `SCL.xsd` (root element and top-level structure), `SCL_IED.xsd`, `SCL_Communication.xsd`, `SCL_DataTypeTemplates.xsd`, `SCL_Substation.xsd`, `SCL_BaseTypes.xsd`, `SCL_BaseSimpleTypes.xsd`, and `SCL_Enums.xsd` — and these are published as the authoritative set by IEC/CENELEC and mirrored by the CoMPAS open-source project; there is no single separate "edition switch" file — instead, tools select the correct rule-set by reading the version/revision attributes on the `<SCL>` root (see prior section) since the base schema file names/namespace are stable across the 2007-era editions.

### Cited Findings
- A 2013 CIRED seminar presentation gives the schema file breakdown: `SCL_Enums.xsd`, `SCL_BaseSimpleTypes.xsd`, `SCL_BaseTypes.xsd`, `SCL_Substation.xsd`, `SCL_Communication.xsd`, `SCL_IED.xsd`, `SCL_DataTypeTemplates.xsd`, and `SCL.xsd` (described as "the main SCL schema syntax definition, which defines the root element of each SCL file") — [CIRED-02 presentation](https://mail.ho-cired.hr/images/SEMINARI/2013_primjena_norme/CIRED-02.pdf).
- IEC 61850-6:2009/AMD1:2018's published schema package matches that same file list — [iTeh standards catalog entry](https://standards.iteh.ai/catalog/standards/iec/79b75107-5dc2-454a-9f11-25844c133dce/iec-61850-6-2009-amd1-2018).
- EN 61850-6:2010 places the XSD set in Annex A, explicitly marked "normative," and states it is identical to IEC 61850-6:2009 — [shop.standards.ie listing](https://shop.standards.ie/en-ie/standards/en-61850-6-2010-348624_saig_cenelec_cenelec_796561).
- The CoMPAS project maintains an open-source mirror repository of the official IEC 61850-6 SCL XSD files, `com-pas/compas-scl-xsd` — [ecosyste.ms project listing](https://awesome.ecosyste.ms/projects/github.com%2Fcom-pas%2Fcompas-scl-xsd).
- Validation beyond XSD is now formally standardized: IEC TS 61850-6-3:2025, "Format of machine-processable rules for validation of IEC 61850 XML-based files," was published by IEC TC57 WG10, and a companion CIGRE paper is titled "Introduction to IEC 61850-6-3 OCL machine-processable rules for validation of IEC 61850 XML-based files," explicitly stating OCL rules "go beyond the capabilities of XML Schema Definitions (XSD)" — [IEC TS 61850-6-3:2025 catalog entry](https://standards.iteh.ai/catalog/standards/iec/c9feba2a-c0b5-431a-9037-f867acf184c7/iec-ts-61850-6-3-2025); [CIGRE B5-11423-2024 paper listing](https://www.e-cigre.org/publications/detail/b5-11423-2024-introduction-to-iec-61850-6-3-ocl-machine-processable-rules-for-validation-of-iec-61850-xml-based-files.html).

### Inferences
- A new SCL-ingestion tool should treat XSD validation as necessary-but-not-sufficient: a file can be 100% XSD-valid and still be semantically broken (dangling `lnType`, mismatched `datSet` reference, etc.), which is precisely the gap IEC TS 61850-6-3 was created to close via a separate, machine-processable (OCL) rule layer.
- Because the schema files are modular (per-section: IED, Communication, DataTypeTemplates, Substation, base types/enums), a tool can in principle validate/parse sections independently once it has confirmed overall document validity — useful for the "extract a reduced file" performance strategy noted above.

### Gaps
- Did not confirm the exact `xs:import`/`xs:include` dependency graph between the eight schema files (i.e., which file imports which) — would require opening the XSD files directly from the CoMPAS repository.
- Did not find confirmation of the precise attribute name(s) on `<SCL>` that a validator reads to pick edition-specific rules (see prior Gap).

## Validation: semantic/referential-integrity checks beyond XSD

### Takeaway
The standard's own structure requires several categories of cross-reference checks that XSD cannot express (because XSD only validates local syntax, not that an ID string used elsewhere in the document actually resolves): LN/LN0 `lnType` → `LNodeType` existence; DOType/DAType/EnumType internal cross-references; FCDA paths resolving to real DO/DA structure; GOOSE/SMV/Report `datSet` resolving to an actual `DataSet`; and IEC TS 61850-6-3 (2025) now formalizes many of these as OCL rules, implemented so far mainly by RiseClipse and CoMPAS rather than mainstream commercial SCT/ICT tools.

### Cited Findings
- "In several places in an SCL instance file, a reference to another object in the file is specified (e.g., LNode to LN, LN to LNodeType)... the schema requires an existing LNodeType in the DataTypeTemplate for every declared lnType" — summarized from search results describing SCL cross-reference validation (secondary synthesis; exact primary citation not resolved — treat as a well-established community understanding rather than a quoted standard clause).
- "Validating LNodeType contents goes beyond the XSD. Parts 7-3 and 7-4 define mandatory and optional elements, and a check can catch cases such as a logical node of type 'XCBR' does not contain a 'Pos' data" — i.e., per-LN-class mandatory-DO conformance (from 61850-7-4) is a semantic check layered on top of XSD, not expressible in XSD alone.
- IEC TS 61850-6-3:2025 ("Format of machine-processable rules for validation of IEC 61850 XML-based files") was published specifically because "XSD cannot express many of the semantic and cross-referenced constraints required by IEC 61850 SCL" — [CIGRE B5-11423-2024](https://www.e-cigre.org/publications/detail/b5-11423-2024-introduction-to-iec-61850-6-3-ocl-machine-processable-rules-for-validation-of-iec-61850-xml-based-files.html); [IEC TS 61850-6-3:2025](https://standards.iteh.ai/catalog/standards/iec/c9feba2a-c0b5-431a-9037-f867acf184c7/iec-ts-61850-6-3-2025).
- As of early 2026 (per search-result synthesis), RiseClipse and CoMPAS are described as the primary tools implementing OCL-based SCL validation against these rules; most commercial IEC 61850 engineering tools reportedly do not yet implement the IEC TS 61850-6-3 rule sets — this is a secondary-source characterization and should be treated as an inference pending direct confirmation, not a quoted fact.
- A UCA iUG tracker item records that "FCDA references that do not resolve to a DA or BDA in DataTypeTemplates" was an identified gap, addressed in IEC 61850-6 Ed 2.1 / 7-2 Ed 2.1, including a conformance test covering DO hierarchy correctness inside datasets (source: search-result synthesis of UCA redmine tracker content; exact issue number not confirmed by direct fetch — flagged lower confidence).
- Uniqueness rule, cited as IEC 61850-6 §9.2.6: "the combination of iedName, ldInst, prefix, lnClass and lnInst must be unique across substation sections whenever iedName is set" — [UCA iUG issue 5331](https://redmine.ucaiug.org/issues/5331); a related, closed WG10 "future work" item on the same topic is [UCA iUG issue 5940](https://redmine.ucaiug.org/issues/5940), noting the practical consequence that "a single LN cannot serve as the implementation of several LNodes" under that rule, later addressed differently in TR 61850-90-30 (formerly 6-100) via LNodeSpecNaming.
- IEC 61850-7-4 Annex A gives normative rules for multiple LN instances (via an LN instance ID) and multiple data instances, specifically to avoid vendors inventing incompatible private extension/naming schemes — (search-result synthesis citing IEC 61850-7-4 standard structure; not independently fetched from the standard text itself).

### Inferences
- A new ingestion tool's semantic-validation layer should at minimum implement: (1) `lnType` → `LNodeType@id` resolution; (2) recursive `DO@type` → `DOType@id`, `DA/BDA@type` → `DAType@id`, and enumerated `DA@type`/`bType=Enum` → `EnumType@id` resolution; (3) `FCDA` doName/daName path resolution against the owning IED's actual DOType/DAType tree (not just syntactic well-formedness of the path string); (4) `datSet` attribute on `GSEControl`/`SampledValueControl`/`ReportControl` resolving to a `DataSet` with the same parent LN0; (5) the §9.2.6-style naming uniqueness check (iedName+ldInst+prefix+lnClass+inst). Given IEC TS 61850-6-3 now exists as a formal machine-readable rule format, a new tool's validation rule engine should be designed so these checks can eventually be expressed/driven by imported 61850-6-3 rule sets rather than hard-coded, to track future standard updates.

### Gaps
- Could not obtain the literal text of IEC TS 61850-6-3 rules (categories/examples) — only secondary descriptions that it exists and what problem class it addresses; the actual rule catalog would need to be sourced from the IEC TS 61850-6-3:2025 document itself (paywalled/standards-body access).
- Could not confirm current adoption numbers/vendor list for IEC TS 61850-6-3 implementation beyond the RiseClipse/CoMPAS claim, which itself came from a secondary synthesis rather than a directly quoted/dated source.

## Validation: naming/addressing rules (object reference length, valid characters)

### Takeaway
Multiple secondary/vendor sources reference a 64-character limit somewhere in the IEC 61850 naming scheme, but sources disagree on exactly what the 64 characters bound (logical device name vs. object name vs. something else), and no primary standard text (61850-7-2/-6) was retrieved in this session to resolve the discrepancy — this is a confirmed gap that a tool-design effort should close by consulting 61850-7-2 directly before hard-coding a limit.

### Cited Findings
- A patent document states IEC 61850 Edition 2 names must respect "a 64-character limit for the LD name and 11 characters for the LN prefix," adding that the mapping to these parts "needs to respect the naming length restrictions of IEC 61850 (Edition 2)" — [USPTO patent document](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10845399) (patent prose, not the standard itself — lower confidence).
- Beckhoff TwinCAT library documentation (an implementation, not the standard) lists a maximum **object name** length of 64 and a maximum **object reference** length of 255, and shows object references built from IED, LD, LN, DO, and DA levels, with the server name included only at the IED level — [Beckhoff infosys docs](https://infosys.beckhoff.com/content/1033/tf6510_tc3_iec61850/5668402699.html), [related path](https://infosys.beckhoff.com/content/1031/tf6510_tc3_iec61850/5662798219.html).

### Inferences
- The two sources are not necessarily contradictory: it is plausible the 64-character bound applies to the Logical Device name component specifically (IED name + ldInst, or similar) rather than to the full dotted object reference, while 255 is a separate, larger bound on the complete reference string (IED+LD/LN/DO/DA path) as implemented by at least one vendor stack. This should be verified, not assumed, before being encoded as a hard validation rule.

### Gaps
- No primary-standard confirmation of either limit, or of the valid-character set (e.g., whether non-ASCII, hyphens, or leading digits are permitted in IED/LD/LN names) — this entire sub-area needs direct consultation of IEC 61850-7-2 (and/or -6) before implementation.

## Validation: Communication section consistency (ConnectedAP/GSE/SMV cross-references)

### Takeaway
The Communication section is purely referential — every `ConnectedAP` must point to a real `IED`/`AccessPoint` via `iedName`/`apName`, and every `GSE`/`SMV` inside a `ConnectedAP` must point to a real control block inside that IED's LN0 via `ldInst` + `cbName` — so a validating tool must cross-check Communication-section attributes against the IED section's actual tree rather than validating them in isolation.

### Cited Findings
- "Each SubNetwork can have multiple ConnectedAP elements, which serve as pointers to IEDs' AccessPoints, defined by attributes iedName and apName. The iedName must match a target IED's name" (i.e., the `name` attribute of the target `<IED>` element must equal the ConnectedAP's `iedName`) — synthesized from vendor manual and OpenSCD-adjacent search results (see Communication Basics wiki link below); treat as community-standard description rather than a direct standard quote.
- "A GSE element inside a ConnectedAP points to a GOOSE control block through its ldInst and cbName attributes. One GSE element should reference one control block, and different ConnectedAP elements can reference the same block" — same synthesis, referencing GE B30/UR-series manuals' SCL implementation chapters, e.g. [GE B30 manual, GOOSE-via-SCL section](https://www.manualslib.com/manual/1337443/Ge-B30.html?page=486).
- An example SMV element uses `ldInst`/`cbName` attributes plus an `Address` block with typed `P` entries such as MAC-Address, APPID, VLAN-ID, VLAN-PRIORITY — from a CIRED presentation example (illustrative, not standard text) — [CIRED-02 presentation](https://mail.ho-cired.hr/images/SEMINARI/2013_primjena_norme/CIRED-02.pdf).
- OpenSCD's "Communication Basics" wiki page is the closest primary-tool documentation of this cross-referencing model — [OpenSCD wiki, Communication Basics](https://github.com/openscd/open-scd/wiki/Communication-Basics) (page located via search; full content not independently fetched in this session, so treat the bullet above as search-result synthesis pending direct confirmation).
- A UCA iUG tracker discussion flags an open semantic question: whether a `GSEControl` carrying a `datSet` value but with no corresponding Communication-section entry is valid; the standard reportedly does not explicitly declare this either way — [UCA iUG issue 592](https://redmine.ucaiug.org/issues/592).

### Inferences
- A validating ingestion tool should implement at least these Communication-section checks: (1) `ConnectedAP@iedName` exists as an `IED@name`; (2) `ConnectedAP@apName` exists as that IED's `AccessPoint@name`; (3) every `GSE@ldInst`+`GSE@cbName` resolves to a `GSEControl` inside the matching `LDevice`'s `LN0`; (4) every `SMV@ldInst`+`SMV@cbName` resolves similarly to a `SampledValueControl`; (5) flag (as a warning, not necessarily an error, given the open standard ambiguity noted in UCA issue 592) any control block with a `datSet` but no corresponding Communication-section GSE/SMV entry, since this is a known gray area rather than settled.

### Gaps
- Did not obtain an authoritative (standard-text) statement of whether a GSE/SMV entry is mandatory for every control block that has a non-empty `datSet`, or optional — the UCA tracker discussion suggests this is genuinely unresolved/ambiguous in the standard, which a new tool's rule set should treat as a configurable warning rather than a hard validation failure.

## Validation: conformance rules from 61850-6/-7-1/-7-2/-7-3/-7-4 (mandatory LN/DO/DA, CDC structure)

### Takeaway
IEC 61850-7-4 defines, per logical-node class, which Data Objects are Mandatory/Optional/Conditional (M/O/C), and every Logical Device must contain the system logical nodes LLN0 (logical node zero, holding dataset/control-block definitions) and LPHD (physical device); IEC 61850-7-3 defines the internal CDC (Common Data Class) structure (which DAs each CDC-typed DO must contain, again M/O/C by functional constraint); no single open-source or commercial tool was found that comprehensively automates all of these per-class conformance checks against arbitrary SCL input — vendor "conformance statements" (SICS/PICS/MICS/PIXIT style documents) remain the main artifact recording this today, and they are per-device, not per-SCL-file.

### Cited Findings
- IEC 61850-7-4 defines LPHD (physical device) and LLN0 (logical node zero) as system logical nodes; a standards catalog entry for IEC 61850-7-4:2003 lists them among the standard's logical node class definitions — [globalspec IEC 61850-7-4 listing](https://standards.globalspec.com/std/589249/iec-61850-7-4).
- Vendor conformance statements mark each Data Object in a logical node class as mandatory/optional/conditional per 7-4; one GE manual gives LPHD attributes (PhyNam, PhyHealth, Proxy) and LLN0 attributes (Mod, Beh) each tagged M/O/C — [GE 350 manual](https://Manualslib.com/manual/1281367/Ge-350.html?page=722) (vendor documentation, illustrative of the M/O/C pattern rather than the standard text itself).
- "XSD cannot express many of the semantic and cross-referenced constraints required by IEC 61850 SCL," reiterated specifically in the context of per-LN-class mandatory data checks (e.g. an XCBR instance lacking a mandatory "Pos" DO) needing a semantic layer beyond XSD — search-result synthesis citing IEC 61850-7-3/-7-4 structure (see Validation section above).
- No dedicated open-source or commercial SCL/CDC conformance checker specifically for mandatory-DO/DA-by-FC rules was found; available "conformance tools" surfaced in search were IED/client protocol test suites (e.g., a KEPCO/QualityLogic "IEC 61850 Edition 2 Client Verifier" running UCA Edition-2 client test procedures, and a PNNL conformance toolkit covering IEC 62351 security), not SCL-file structural validators — [QualityLogic IEC 61850 Edition 2 Client Verifier](https://qualitylogic.com/wp-content/uploads/2024/11/IEC-61850-Edition-2-Client-Verifier.pdf); [PNNL-22511-1](https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-22511-1.pdf).

### Inferences
- A new SCL-ingestion tool wanting to check 7-3/7-4 conformance would need to encode the per-LN-class M/O/C data tables (from 7-4) and per-CDC M/O/C attribute tables (from 7-3) as its own rule data (there is no evidence of a ready-made open-source machine-readable version of these specific tables, distinct from the newer IEC TS 61850-6-3 cross-reference rules, which address referential integrity rather than CDC/LN-class completeness). This is likely to be one of the more labor-intensive parts of building a conformance-checking SCL tool from scratch.

### Gaps
- Did not find a machine-readable (XML/JSON/OCL) encoding of the 7-3 CDC attribute tables or 7-4 LN-class DO tables; did not find an open-source tool that checks "does this LN instance's DOType actually contain all mandatory DOs for its lnClass per 7-4."

## Validation: known open-source/reference SCL validators

### Takeaway
Confirmed reference implementations/validators found: libiec61850 (mz-automation, C, GPLv3, includes SCL/ICD parsing and a static-model generator), CoMPAS (SCL Consistency Tool / compas-sct, plus the compas-scl-xsd official schema mirror), OpenSCD (browser-based SCL editor, schema-validates on load/save), and — specifically for the new machine-processable rule format — RiseClipse and CoMPAS as the tools implementing IEC TS 61850-6-3 OCL rules; several smaller/alternative parsers exist (Go `go-iec61850`, Python `pySCD`, Rust `surge-io`) but with less evidence of conformance-rule depth.

### Cited Findings
- libiec61850: official repo under mz-automation (GitHub, ~1.17k stars per a release-tracking mirror page), GPLv3-licensed; includes a Static Model Generator that parses SCL/ICD and generates C model code — [MZ Automation GitHub org](https://www.github.com/mz-automation); [DeepWiki summary](https://deepwiki.com/mz-automation/libiec61850/5-data-model) (secondary summary).
- CoMPAS: hosts `compas-scl-xsd` (the official IEC 61850-6 SCL XSD schema mirror) and `compas-sct` (SCL Consistency Tool, with documented large-file-handling guidance) — [compas-scl-xsd listing](https://awesome.ecosyste.ms/projects/github.com%2Fcom-pas%2Fcompas-scl-xsd); [compas-sct docs](https://com-pas.github.io/compas-sct/compas-sct.html).
- OpenSCD: open-source, plug-in-based, progressive-web-app SCL editor; keeps all project state as SCL XML validated against the schema; closely related to, but organizationally separate from, CoMPAS — [LF Energy OpenSCD description](https://lfenergy.org/?p=9187); [OpenSCD FOSDEM 2024 talk](https://fosdem.org/schedule/event/fosdem-2024-1956-openscd-everything-everywhere-all-at-once).
- RiseClipse and CoMPAS are named (via search-result synthesis, not a directly fetched primary statement) as the tools currently implementing IEC TS 61850-6-3 OCL-based validation rules, with most commercial SCT/ICT tools reportedly not yet implementing this rule set.
- Alternative/smaller parsers found: Go `go-iec61850` (SCD/ICD/CID/IID tooling) — [pkg.go.dev](https://pkg.go.dev/github.com/otfabric/go-iec61850); Rust `surge-io` crate with an SCL parser module (PolyForm Noncommercial license) — [docs.rs](https://docs.rs/crate/surge-io/0.1.9/source/src/scl.rs); Python `pySCD` (GUI + library SCD parser, described in a Chinese-language paper per search synthesis, primary paper not fetched).

### Inferences
- For a new SCL-ingestion tool, the most useful existing reference material to study directly (not just cite) would be: `compas-scl-xsd` (ground-truth schema files across editions), `compas-sct` (documented large-file strategy and consistency-check scope), and libiec61850's static-model-generator approach (type/instance join strategy, even though it targets runtime MMS server construction rather than general SCD ingestion).

### Gaps
- Could not browse the libiec61850 or compas-sct source trees directly in this read-only research session (only secondary/summary pages were reachable), so implementation-level detail (exact function names, algorithms) beyond what DeepWiki's summary states is unconfirmed and should be verified by direct source inspection before a new tool copies any specific approach.

## Structure: SCL containment hierarchy

### Takeaway
SCL instance data splits into two parallel trees that are joined by ID reference rather than XML containment: the **Substation hierarchy** (Substation > VoltageLevel > Bay > ConductingEquipment/LNode, physical/single-line-diagram-oriented) and the **IED hierarchy** (IED > AccessPoint > Server > LDevice > LN0/LN > DOI > DAI, the actual device/data-instance configuration), plus a wholly separate **DataTypeTemplates** section (LNodeType > DO > [referencing] DOType > DA/SDO > [referencing] DAType/EnumType/BasicType) that both other trees reference by ID string rather than contain.

### Cited Findings
- OpenSCD's own documentation describes an SCL file as containing a Header, Substation, Communication, IED, and DataTypeTemplates section, and states that within DataTypeTemplates "LNodeType, DOType, DAType, and EnumType each build on the one below them" — [LF Energy / OpenSCD description](https://lfenergy.org/?p=9187); [OpenSCD GitHub wiki, DataTypeTemplates](https://github.com/com-pas/compas-open-scd/wiki/DataTypeTemplates).
- The same wiki page states the nesting pattern: "LNodeType contains DO; DOType contains SDO and DA; DAType contains BDA; EnumType contains EnumVal," and that dependency/definition order is bottom-up (LNodeType depends on existing DOTypes, DOTypes depend on existing DATypes, enumerated attributes depend on existing EnumTypes) — [OpenSCD wiki, DataTypeTemplates](https://github.com/com-pas/compas-open-scd/wiki/DataTypeTemplates).
- Four SCL file "flavors" share this identical overall structure: SSD, SCD, ICD, and CID (differing in which sections are populated/required, not in schema shape) — [OpenSCD description](https://lfenergy.org/?p=9187).

### Inferences
- The Substation-section hierarchy (physical plant topology, with `LNode` elements that reference actual LN instances inside IEDs) and the IED-section hierarchy (actual device configuration) are deliberately decoupled: `LNode` in the Substation section is a *reference* pointer (via `iedName`/`ldInst`/`prefix`/`lnClass`/`lnInst`) into the IED tree, not a duplicate container — this lets one IED's logical nodes be "mapped onto" multiple primary-equipment locations in the single-line diagram without copying data.

### Gaps
- Did not independently verify the exact child-element cardinality/attribute list for `LNode` (Substation section) linking to IED-section LN instances — recommend confirming directly against `SCL_Substation.xsd`.

## Structure: instance (DOI/DAI) vs. type definition (DataTypeTemplates) and how a tool joins them

### Takeaway
SCL strictly separates "what the data model shape is" (DataTypeTemplates: LNodeType/DOType/DAType/EnumType, each identified by an `id` and referenced elsewhere by that `id` string) from "what values/instance-level configuration exist" (DOI/DAI under an LDevice's LN/LN0, which override/populate the shape as needed); a parsing tool must perform an explicit join step at load time: resolve each LN/LN0's `lnType` attribute to a `LNodeType@id`, then walk that LNodeType's `<DO name=... type=...>` children to `DOType@id`, then that DOType's `<DA name=... type=...>`/`<SDO ... type=...>` children to `DAType@id` (recursively) or `EnumType@id`/basic type, building a fully resolved object model; only after this join can a DOI/DAI instance override be matched to the correct position in that resolved shape.

### Cited Findings
- From the OpenSCD DataTypeTemplates wiki page (search-result synthesis, since the page itself gave only a high-level description on direct fetch): the hierarchy descends LN → DO → DA, with enumerations at the bottom, and "this hierarchical structure is defined in the DataTypeTemplates section of an SCL file," built bottom-up by ID dependency — [OpenSCD wiki, DataTypeTemplates](https://github.com/com-pas/compas-open-scd/wiki/DataTypeTemplates).
- Community/search-result synthesis on semantic validation explicitly frames this as a reference-resolution problem the schema itself cannot guarantee: "the schema requires an existing LNodeType in the DataTypeTemplate for every declared lnType" — i.e., XSD enforces that `lnType` is a string of the right type, but not that a matching `LNodeType/@id` exists; that join/resolution is left to the application (see Validation section above).
- libiec61850's Static Model Generator is described (secondary DeepWiki summary) as parsing an SCL/ICD file and "generating C code that defines the data model structure" — i.e., it performs exactly this type/instance join once, at build/generation time, producing a flattened, pre-resolved static structure for runtime use rather than re-resolving references at runtime — [DeepWiki summary](https://deepwiki.com/mz-automation/libiec61850/5-data-model).

### Inferences
- The precise join algorithm a new tool should implement is: (1) index all `LNodeType`, `DOType`, `DAType`, `EnumType` elements by `id` from DataTypeTemplates; (2) for each `LN`/`LN0` instance, look up `LNodeType[@id = LN/@lnType]`; (3) for each `<DO>` child of that LNodeType, look up `DOType[@id = DO/@type]`; (4) recursively, for each `<DA>`/`<SDO>` child of that DOType, resolve `DA/@type` → `DAType[@id=...]` (if `bType="Struct"`) or to a basic type / `EnumType[@id = DA/@type]` (if `bType="Enum"`); (5) only once this full shape is resolved should the tool overlay the LDevice's actual `<DOI>`/`<DAI>` (and nested `<SDI>`) instance elements, matching each `DOI@name`/`DAI@name` (and `DAI@ix` for arrays, `sAddr`, `valImport`, etc.) onto the corresponding node in the resolved shape, applying any `DAI/Val` override values.
- Because this join is purely ID-string-based (no XML containment/ownership between DataTypeTemplates and the IED/Substation trees), a single `LNodeType`/`DOType`/`DAType` definition is normally shared/reused by many LN instances across many IEDs in the same SCD file — an important memory/performance consideration (resolve each type once, cache it, reference the cached resolved shape from every instance that uses it, rather than re-resolving per instance).

### Gaps
- Did not confirm the exact attribute names for array-indexed DAI overrides (`ix`) or the precedence rules when both a DOType-level default `Val` and an instance-level `DAI/Val` are present — would need direct reference to IEC 61850-6 clause text on DOI/DAI/SDI/Val semantics.

## Structure: full object/data path construction and resolution algorithm

### Takeaway
A full SCL/MMS-style object reference is built by concatenating, in order, the IED name, the Logical Device instance, the Logical Node name (prefix + lnClass + inst), then the Data Object path (DO name, plus any nested SDO names), then optionally a Data Attribute path (DA name, plus any nested BDA names), with the Functional Constraint (FC) typically carried as a separate, out-of-band qualifier (not part of the dotted name string itself) used to select which "view" of the data (e.g. ST, MX, CF, SP) a client is addressing; confirmed component order came from a vendor implementation (Beckhoff) rather than the standard text directly.

### Cited Findings
- Beckhoff TwinCAT library documentation shows object references built from IED, LD, LN, DO, and DA levels in that order, with the server/IED name included only once at the top (IED) level — [Beckhoff infosys documentation](https://infosys.beckhoff.com/content/1033/tf6510_tc3_iec61850/5668402699.html).
- The IEC 61850-6 uniqueness rule (§9.2.6, per UCA iUG tracker) establishes that an LN's full identity within an IED is the tuple (iedName, ldInst, prefix, lnClass, lnInst) — confirming that the LN "name" component of the path is itself composite (prefix + lnClass + instance number), not a single opaque string — [UCA iUG issue 5331](https://redmine.ucaiug.org/issues/5331).
- DataTypeTemplates nesting (LNodeType→DO→DOType→[SDO|DA]→DAType→BDA) establishes that both DO and DA segments of a path can themselves be multi-component (an SDO chain under a DO, a BDA chain under a DA) before the leaf is reached — [OpenSCD wiki, DataTypeTemplates](https://github.com/com-pas/compas-open-scd/wiki/DataTypeTemplates).

### Inferences
- A conservative, standard-aligned construction grammar, synthesized from the above building blocks (not a direct standard quote, so should be checked against 61850-7-2 directly) is:
  `objectReference = IEDName "/" LDInst "/" [prefix] lnClass lnInst "." doName {"." sdoName} ["." daName {"." bdaName}] ["[" FC "]"]`
  i.e., IED name and LD instance are slash-separated; LN prefix+class+inst is a single concatenated token; DO/SDO/DA/BDA segments are dot-separated; FC, when needed for addressing, is appended as a bracketed qualifier rather than a dotted segment. A new ingestion tool should treat FC as metadata resolved from the DOType/DAType definition (each DA has an `fc` attribute in its DAType/DOType definition) rather than something the user supplies ad hoc — i.e., FC is derived by looking up which functional constraint the resolved DA carries in its type definition, not stored per-instance.

### Gaps
- Did not retrieve the literal IEC 61850-7-2 grammar/BNF for the object reference string (exact separator characters, whether LD name = IEDName+ldInst concatenated vs. slash-joined, whether array indices use `(n)` or `[n]`) — this is the single highest-value primary-text confirmation still needed before implementing a parser's path-construction logic; recommend sourcing IEC 61850-7-2 clause 8 (or current edition's equivalent) directly.

## Structure: Communication section cross-references into the IED section

### Takeaway
(Covered in detail under "Validation: Communication section consistency" above — restated here for the structure question): `ConnectedAP@iedName`/`@apName` resolve to `IED@name`/`AccessPoint@name`; `GSE@ldInst`/`@cbName` and `SMV@ldInst`/`@cbName` resolve to a `GSEControl`/`SampledValueControl` inside the `LN0` of the `LDevice@inst = ldInst` within that IED — these are the only links between the Communication section and the IED section; there is no containment, only attribute-based cross-reference.

### Cited Findings
- See citations under "Validation: Communication section consistency" above (GE B30 manual GOOSE-via-SCL chapter, CIRED-02 presentation SMV example, OpenSCD Communication Basics wiki, UCA iUG issue 592).

### Inferences
- See inferences under "Validation: Communication section consistency" above — the join algorithm for a new tool is effectively: index IEDs by name, index each IED's AccessPoints by name, index each LDevice's LN0 control blocks (GSEControl/SampledValueControl/ReportControl) by name per LDevice `inst`; then for every ConnectedAP/GSE/SMV element, perform these three lookups and flag any that fail.

### Gaps
- Same as the Validation section's Gaps: no primary-standard text confirming mandatory-vs-optional status of the GSE/SMV Communication entry relative to a control block's existence.

## Structure: DataSet/FCDA/GSEControl/SampledValueControl/ReportControl relationships, and pub/sub modeling (ExtRef)

### Takeaway
`DataSet` (a named ordered list of `FCDA` data-reference entries) is the single shared payload definition referenced by name (`datSet` attribute) from `GSEControl` (GOOSE), `SampledValueControl` (Sampled Values), and `ReportControl` (Reports); all of these — the DataSet and the control blocks that reference it — live inside the *same* `LN0` of the publishing IED's `LDevice` (they must share the same parent), meaning the publish side is modeled entirely within one IED's own LN0; the subscribe side is modeled separately and asymmetrically via `ExtRef` elements (Edition-2-oriented "Inputs" binding) inside the *subscribing* IED's own LN/LN0, which point back at the publisher's control block by `iedName`/`srcLDInst`(or `ldInst`)/`srcLNClass`/`srcCBName`(or `cbName`) rather than the publisher's SCL containing any reference to its subscribers.

### Cited Findings
- "SampledValueControl must reside in the LN0 element, and both SampledValueControl and its referenced DataSet must share the same parent" — [OpenSCD/LF Energy Sampled Values Basics wiki](https://github.com/openscd/open-scd/wiki/Sampled-Values-Basics).
- "GSEControl also uses `datSet` to name its data set... a GOOSE data set can hold any number of FCDA elements up to the number the IED is capable of" — [OpenSCD wiki material, Edit GOOSE Control Blocks](https://github.com/openscd/open-scd/wiki/Edit-GOOSE-Control-Blocks).
- "A report control block is needed to send the signals in a data set to clients... there are two types: unbuffered and buffered" — [search synthesis of OpenSCD/vendor ReportControl documentation].
- "Data sets are part of a logical node and are most likely included in the LLN0" — [search synthesis].
- Subscription/pub-sub modeling: "In SCL, the receiving IED's input is modeled by an ExtRef element, and subscribing means creating or updating that element" — [OpenSCD/CoMPAS Subscriber Basics wiki](https://github.com/com-pas/compas-open-scd/wiki/Subscriber-basics).
- ExtRef attributes identifying the sender: `iedName`, `srcLDInst`, `srcLNClass`, `srcCBName` point to the sending GOOSE control block — [GE G2/B30 manual, "Implementation model for GOOSE configuration via SCL"](https://www.manualslib.com/manual/1337443/Ge-B30.html?page=490); an OpenSCD example uses `serviceType="GOOSE"` on the ExtRef.
- ExtRef can be "predefined" with an `intAddr` attribute and bound to a source later, though the OpenSCD wiki notes that at the time of that page this later-binding feature was not yet implemented in OpenSCD itself — [OpenSCD Subscriber Basics wiki](https://github.com/openscd/open-scd/wiki/Subscriber-basics).
- UCA iUG tracker discussion confirms ExtRef was the IOP (Interoperability) group's chosen subscription mechanism and that the required ExtRef format was historically under-specified, causing inconsistent tool configurations; a proposal exists (recorded in the tracker) to tighten ExtRef specification in a future edition — [UCA iUG issue 445](https://redmine.ucaiug.org/issues/445?tab=notes), [issue 461](https://redmine.ucaiug.org/issues/461?tab=notes).
- A secondary source (tool write-up) states Edition 2 "binds external signals through Inputs tags, and the remote IED must be present in the SCD file," implying ExtRef/Inputs-based subscription modeling is an Edition-2-oriented mechanism (Edition 1 lacked a standardized SCL-level subscription/input-binding construct) — [Scribd write-up](https://www.scribd.com/document/630104303/writeup) (secondary source, flagged lower confidence; should be checked against 61850-6 Edition 2 text directly).

### Inferences
- The overall ownership/relationship graph a new tool's object model should capture: `LN0` owns zero-or-more `DataSet` elements (each a named, ordered list of `FCDA`); `LN0` also owns zero-or-more `GSEControl`/`SampledValueControl`/`ReportControl` elements, each of which references exactly one `DataSet` by name via its `datSet` attribute (and must be validated as sharing the same parent LN0 as that DataSet); separately, any `LN`/`LN0` (in the *same or a different* IED) may own `Inputs` containing `ExtRef` elements that reference another IED's control block by name (not by containment) — so GOOSE/SV publish-subscribe is a same-IED ownership relationship (control block → dataset) plus a cross-IED, attribute-based pointer relationship (subscriber's ExtRef → publisher's control block), never a bidirectional/contained relationship within a single SCL subtree.
- Because ExtRef historically had an under-specified/loosely enforced format (per the UCA iUG tracker discussion), a new ingestion tool's validation of ExtRef-based bindings should be more lenient/advisory (warn on unresolved ExtRef targets) rather than treating every unresolved ExtRef as a hard document-invalid error, especially for Edition 1-originated or partially-engineered (ICD-only, not yet fully wired into an SCD) files.

### Gaps
- Did not confirm from primary standard text whether `ExtRef` is formally absent from Edition 1 SCL schema entirely, or merely unused by convention — the "Edition 2 binds... via Inputs tags" claim came from a secondary/tool-vendor source only.
- Did not confirm the complete, current attribute list on `ExtRef` (the sources gave `iedName`, `srcLDInst`, `srcLNClass`, `srcCBName`, `serviceType`, `intAddr` — there may be additional attributes such as `desc`, `pDO`, `pDA`, `pLN`, `pServT` describing the *local* bound data point that were not covered in the sources retrieved) — recommend direct confirmation against `SCL_IED.xsd`/the standard text.
