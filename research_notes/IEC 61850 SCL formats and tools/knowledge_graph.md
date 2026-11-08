# IEC 61850 SCL as a Graph Knowledge Base — Research Notes

> **Plan-mode note:** This session is running in plan mode, which restricts me to read-only tools plus edits to this plan file. The research below was completed using read-only web search/fetch tools only. The full content is written here; it still needs to be copied to the requested destination — `D:\Trivium-Inhouse\SCD-POC\research_notes\IEC 61850 SCL formats and tools\knowledge_graph.md` — which requires leaving plan mode (a Write to a new path outside the plan file) and explicit confirmation to proceed with that write.

---

## Part A — Prior Art Survey

### Key Question 1: Has anyone built an IEC-61850-specific ontology or graph model (as opposed to CIM)?

#### Takeaway
Yes, but it is a thin and mostly academic body of work, not an industry-standardized ontology. The earliest and most direct hit is Uslar & Rohjans (OFFIS, 2009), who built an ontology for the IEC 61850 family specifically to integrate it with the IEC 61970 (CIM) ontology; later work (Yang et al., IECON 2015) builds an IEC 61850 ontology and layers a *graph* representation of protection schemes on top of it to auto-generate IEC 61499 function blocks. The most recent work (2025–2026) treats IEC 61850 as one layer inside a larger CIM-rooted or cyber-physical ontology rather than giving it a standalone graph schema. No published, reusable "IEC 61850 OWL ontology" artifact (e.g., a downloadable `.owl`/`.ttl` file analogous to the CIM RDFS/OWL files) turned up in search.

#### Cited Findings
- Mathias Uslar and Sebastian Rohjans (OFFIS), "Ontology-based Integration of the Heterogeneous Standards IEC 61970 and 61850," Internationaler ETG-Kongress 2009 (Düsseldorf, 27–28 Oct 2009): describes building an ontology for the IEC 61850 family and bridging changes between it and an existing IEC 61970 (CIM) ontology via a "mediation bridge" — [OFFIS](https://www.offis.de/en/offis/publication/ontology-based-integration-of-the-heterogeneous-standards-iec-61970-and-61850.html), [VDE Verlag listing](https://vde-verlag.de/proceedings-en/453194053.html). Uslar's PhD thesis (defended Oct 2009) covers this same integration-of-heterogeneous-standards work — [buchfreund.de author page](https://www.buchfreund.de/de/autor/mathias-uslar).
- Uslar and Grüning, "A Use Case for Ontology Evolution and Interoperability: The IEC Utility Standards Reference Framework 62357" (book chapter, ~2010): proposes a solution based on the "COLIN" ontology-evolution framework for integrating IEC 61970 and IEC 61850 — [IGI Global](https://www.igi-global.com/chapter/use-case-ontology-evolution-interoperability/69121), [irma-international.org](https://irma-international.org/teaching-case/use-case-ontology-evolution-interoperability/38044).
- Yang et al., IECON 2015 (9–12 Nov 2015, Yokohama): proposes representing an IEC 61850 protection scheme as a graph, then integrating that graph into a previously-developed IEC 61850 ontology; the graph/ontology combination is used to generate IEC 61499 function-block networks with logical-node-to-logical-node connections; case study is a "sympathetic tripping" protection scenario. The paper's own framing is that the IEC 61850 standard does not formally capture logical-node-to-logical-node message passing, which is why a supplementary graph model was needed — [IECON abstract via Unpaywall](https://unpaywall.org/10.1109%2FIECON.2015.7392317). A related (but distinct) arXiv paper on IEC 61499 function blocks for substation automation describes a similar GOOSE-based trip scenario — [arXiv:1508.06435](https://arxiv.org/pdf/1508.06435).
- IEC TS 61850-7-7:2018, "Engineering access for IEC 61850-based systems — Machine processable format for IEC 61850 data models and configurations," defines a *machine-processable* (not graph/ontology) representation of the standard's own LN/CDC tables for tool use — [GlobalSpec reference](https://reference.globalspec.com/ref/4470004/iec-ts-61850-7-7-2018). This is standards-body machine-readability infrastructure, not a knowledge graph.
- Nachabe, Lefrançois, Zimmermann (Mines Saint-Étienne) and Effantin (EDF), SEMANTiCS 2025 poster (CEUR-WS Vol-4064, PD-paper1): describes an ETL pipeline converting IEC-61850-tagged solar-plant data into a knowledge graph conforming to the "Omega-X" project ontology, loaded into GraphDB. Their framing (per search-result summary, full PDF text was not machine-readable) is that IEC 61850 provides consistency at the data-exchange/syntax level but does not by itself deliver full semantic interoperability — hence the extra ontology layer — [CEUR-WS PD-paper1.pdf](https://ceur-ws.org/Vol-4064/PD-paper1.pdf) (PDF text could not be extracted by automated fetch; treat authorship/venue as confirmed, substantive claims as a secondary paraphrase from search snippets, not independently verified against full text).
- Sankaranarayanan, Mandulak, Shahbaz, Hammad, "Towards Cyber-Physical Cognition: A Unified Ontology-Driven Knowledge Graph for Real-Time Autonomous Grid Operations" (arXiv 2608.16001, 2025/2026): per search-result summary, proposes a four-layer ontology rooting cyber-layer classes (IEC 61850/IEC 62351) under `cim:IdentifiedObject` so that IEC 61850 cyber/SCADA concepts and CIM physical-asset concepts share one schema without a post-hoc alignment step — [arXiv:2608.16001](https://arxiv.org/pdf/2608.16001) (full PDF text was not machine-readable via automated fetch; this description should be treated as a secondary paraphrase, not independently verified).
- KTH master's thesis listing on "Automated configuration of digital substation infrastructure using IEC 61850 SCL files" and a separate KTH lecture/thesis-topic listing describing conversion of a substation Ethernet network description into a graph (devices and ports as vertices; device-to-port and port-to-port edges; port groups to represent redundant paths) — [KTH thesis listing](https://www.kth.se/epe/calendar/exjobb/automated-configuration-of-digital-substation-infrastructure-using-iec-61850-scl-files-1.1481537). This is a thesis-topic/presentation listing, not a published, peer-reviewed method, and does not name a specific graph database.

#### Inferences
- There is no single, citable, widely-adopted "IEC 61850 ontology" or "IEC 61850 graph schema" that functions the way CIM's OWL/RDFS profiles function for ENTSO-E. Every piece of prior art either (a) builds a one-off academic ontology to solve a specific integration or code-generation problem, or (b) treats IEC 61850 as a subordinate layer glued onto a CIM-rooted model. This means a graph model proposed for SCL content (Part B below) is a **reasoned proposal**, not an implementation of an existing standard or de-facto community schema.
- The recurring theme across 2009–2026 sources is that IEC 61850's own data model (LN/DO/DA hierarchy) is not graph-shaped by the standard's own design — it is a strict containment hierarchy plus string-based references (e.g., `Val` text referencing LNodeType names, ExtRef `iedName`/`ldInst`/`prefix`/`lnClass`/`doName` tuples) — and every piece of prior art that turns it into a graph does so by *adding* an external layer (ontology, bridge, or ad-hoc graph structure) on top of the hierarchy, not by finding graph structure already native to the standard.

#### Gaps
- No source provided a downloadable/citable IEC 61850 OWL/RDFS ontology file analogous to the CIM's. If one exists (e.g., inside IEC TS 62361-102 or a TC57 WG19 deliverable), it was not surfaced by these searches and would need direct access to IEC/TC57 working documents, which are typically paywalled/members-only.
- The Omega-X and cyber-physical-cognition papers could not be read in full text (PDF extraction failed both times); their architecture claims above are secondary paraphrases from search-engine summaries and should be re-verified against the primary PDFs before being treated as settled fact in a final report.
- No source gave a worked, publicly documented example of SCL (SCD/ICD) files loaded into Neo4j, Memgraph, Neptune, or any named property-graph product. The closest hits (KTH thesis topics, vendor marketing from Verance AI) are not peer-reviewed or are explicitly marketing claims with "no independent evidence" (see Key Question 3 below).

---

### Key Question 2: What CIM-to-graph / CIM-to-RDF prior art exists, and how does the IEC 61850–CIM "harmonization" effort bear on ontology design? (Adjacent, not IEC-61850-specific)

#### Takeaway
CIM (IEC 61970/61968) has mature, standardized RDF/OWL tooling in production use at ENTSO-E (CGMES), which is the strongest piece of adjacent prior art for "power-system-data-as-a-graph." A parallel, decade-long but less mature IEC TC57 effort ("CIM–IEC 61850 harmonization," IEC TS 62361-102) has tried to define a common UML super-model so that CIM-graph tooling could, in principle, also cover IEC 61850 concepts — but this harmonization layer is still described in recent (2024-era) IEC committee communications as proposals/questionnaires rather than a finished, widely implemented standard.

#### Cited Findings
- ENTSO-E has adopted IEC CIM as the mandatory format for cross-border grid-model exchange in Europe, under the profile name CGMES (Common Grid Model Exchange Standard) — [ENTSO-E RDF-SyntaxUserGuide v1.1.0 (2024-04-04)](https://eepublicdownloads.entsoe.eu/clean-documents/CIM_documents/Grid_Model_CIM/RDF-SyntaxUserGuide_v_1-1-0.pdf), [OpenCGMES background](https://opencgmes.soptim.de/reference/cgmes-background), earlier [RDF-SyntaxUserGuide v1.0](https://www.entsoe.eu/Documents/CIM_documents/Grid_Model_CIM/RDF-SyntaxUserGuide_v1-0.pdf).
- Actual CIM grid-model data is exchanged as "CIMXML" files — an RDF/XML serialization standardized by IEC 61970-552 — and RDFS/OWL ontologies plus SHACL shapes are derived from the underlying CIM UML models (per a secondary slide-deck source, not an IEC primary document) — [search-aggregated slide deck](https://docs.google.com/presentation/d/1ktXSCo3akYUnZH2ZKGs8CfpmnMWYtnui/htmlpresent).
- A 2026 CIGRE paper (D2-12614-2026), "From Documents to Knowledge Graphs: Intelligent Requirements Management Using CIM-Based Ontology," applies CIM-based OWL ontologies with SPARQL querying to requirements management — [CIGRE e-library listing](https://www.e-cigre.org/publications/detail/d2-12614-2026-from-documents-to-knowledge-graphs-intelligent-requirements-management-using-cim-based-ontology.html) (listing/abstract only; full text not retrieved).
- IEC TS 62361-102:2018, "Power systems management and associated information exchange — Guidelines for harmonization — Part 102: CIM-IEC 61850 harmonization," proposes adapting/extending existing information models (or defining new ones) to improve CIM–IEC 61850 communication — [IEC webstore listing](https://webstore.iec.ch/publication/27417).
- A NASPI reference document ("Harmonizing the International Electrotechnical...") describes a proposed common, unified UML model that extends the CIM UML model — recognized by TC57 as the preferred approach for common semantics — intended to generate *both* CIM-XML and IEC 61850 SCL-XML outputs from one source model — [NASPI PDF](https://naspi.org/sites/default/files/reference_documents/cim_61850_harmonized_model_for_smart_grid.pdf) (fetch attempt returned HTTP 429; title/approach description is from the search-engine summary only and was not independently verified against the full document — treat as a **gap**, not a confirmed finding).
- PacWorld ("IEC TC57 Industry Updates") reports that, as of a (unconfirmed-date, apparently ~2024) circulation, IEC was polling national committees on two proposals: (1) converting TS 62361-102 into a full International Standard, including exporting CIM-based models as inputs to IEC 61850 System Specification Documents (SSDs); and (2) a new technical specification, IEC 62361-105, on harmonization for automation and protection — [pacw.org](https://www.pacw.org/?p=10456), [pacw.org WG17 update](https://www.pacw.org/iec-tc-57-wg-17-update-13). Work is also described as ongoing to map IEC 61850 DER data models into CIM, and to extend CIM with function-block classes corresponding to IEC 61850 logical nodes or tight LN groups.
- An older (2011) Korean conference paper reported that IEC TC57 WG19 activity was minimal at that time, with EPRI running harmonization work since 2009 — [koreascience.kr](https://koreascience.kr/article/CFKO201133254116584.pdf). No current (2025/2026) status for WG19 itself was found; the PacWorld items above are the most recent harmonization-status evidence located.
- Santodomingo, Rohjans, Uslar, Rodríguez-Mondéjar, Sanz-Bobi published a sequence of CIM–IEC 61850 ontology-matching papers: (a) IEEE SmartGridComm 2010 — ontology matching to resolve CIM/IEC 61850 mismatches, plus the open-source "ESODAT" tool that applies OWL alignments to translate configuration files between the two standards without modifying either original standard — [Comillas IIT listing](https://iit.comillas.edu/publicacion/congreso/en/10897/Ontology%20matching%20approach%20to%20the%20harmonization%20of%20CIM%20and%20IEC%2061850%20standards); (b) SmartGridComm 2011, "Towards the automatic alignment of CIM and SCL ontologies" — combines "CIMMappingBench" and "ESODAT" with a new "Domain Expert" component adding electric-system domain knowledge to find further alignments, tested on a simple facility's configuration file — [Comillas IIT listing](https://iit.comillas.edu/publicacion/congreso/en/10978/Towards%20the%20automatic%20alignment%20of%20CIM%20and%20SCL%20ontologies); (c) IEEE Transactions on Power Systems, 2013, vol. 28 no. 4, pp. 4348–4355, "Facilitating the automatic mapping of IEC 61850 signals and CIM measurements" — applies ontology matching to *run-time signal* mapping between the two standards, explicitly stating that without it, signal mapping must be done manually; evaluated against four substation architectures — [IIT Comillas preview PDF](https://www.iit.comillas.edu/documentacion/revista/IIT-13-065A_preview/Facilitating%20the%20automatic%20mapping%20of%20IEC%2061850%20signals%20and%20CIM%20measurements.pdf).

#### Inferences
- The CIM/CGMES RDF-OWL/SHACL/SPARQL stack is the single strongest piece of real-world evidence that an IEC-power-system standard can be represented and queried as RDF at production scale in a regulated, multi-vendor, cross-border setting (ENTSO-E). It is legitimate adjacent prior art for "should SCL be modeled as RDF/OWL," but it is **CIM**, not **IEC 61850**, and the harmonization-layer status (still proposal/questionnaire-stage per 2024-era TC57 updates) means there is currently no finished, ratified ontology that losslessly maps SCL concepts into the CIM/CGMES RDF world — a graph-model designer cannot simply "reuse CGMES" for SCL content today without doing the same kind of ad-hoc alignment the Santodomingo/Uslar/Rohjans line of papers had to do by hand.
- Because the harmonization work's own stated goal is a common UML model that emits both CIM-XML and SCL-XML, any serious "align SCL with existing power-system ontologies" effort should track IEC TS 62361-102 (and the proposed 62361-105) rather than inventing a parallel mapping from scratch — but this is a standards-watching recommendation, not something already built and citable today.

#### Gaps
- Could not retrieve the NASPI harmonization PDF's full text (429 error on refetch); its "common UML model" description above rests on a search-engine paraphrase only.
- Could not confirm current (2025/2026) status of IEC TC57 WG19 or whether TS 62361-102 has since been promoted to a full IS, or whether 62361-105 has been formally registered as a work item — the PacWorld items are the most recent but their exact publication date was not confirmed by the search tool.
- No official, downloadable CIM OWL/RDFS schema file location was found in these searches (only guides referencing their existence); a report-writer wanting to cite the artifact directly should consult the ENTSO-E CIM documents page or IEC 61970-600 series directly.

---

### Key Question 3: What industry/whitepaper evidence exists for "digital substation" or "digital twin" architectures using a graph database, and how credible is it?

#### Takeaway
There is real but thin evidence: one peer-reviewed-adjacent conference paper (VDE/EMIE 2022) describing a CIM-ontology-plus-graph-database substation digital twin, one arXiv paper (2019) storing substation CIM/E models in a graph database to auto-generate one-line diagrams, and vendor marketing (Bentley, Verance AI) making broader claims that should be treated skeptically absent independent benchmarks. A notable, more candid technical voice (a Siemens consultant writing on Statnett's public `Talk2PowerSystem` project wiki) argues explicitly that no single database technology (relational, triple-store, or time-series) serves all the query types a power-system knowledge graph needs, including IEC 61850/SCADA queries — an important, realistic caveat for any SCL-graph proposal.

#### Cited Findings
- A 2022 EMIE-conference paper describes a substation digital twin composed of four parts — ontology model, data model, 3D model, and simulation model — with a graph database used specifically to organize how the digital twin's modules connect to each other, supporting situational awareness and operator training — [VDE Verlag listing (EN)](https://www.vde-verlag.de/proceedings-en/565961155.html), [VDE Verlag listing (DE)](https://www.vde-verlag.de/proceedings-de/565961155.html) (title: "Research on Digital Twin System for Power Substation Situation Awareness and Operation Simulation"; listing/abstract only, full text not retrieved).
- A 2019 arXiv paper stores substation CIM/E models in a graph database and auto-generates one-line diagrams from the stored graph; the authors flag that the graph database and the generated front-end diagrams can drift out of sync unless explicitly synchronized — a direct, citable statement of a graph/source-of-truth synchronization risk — [arXiv:1903.09495](https://ar5iv.labs.arxiv.org/html/1903.09495).
- Bentley Systems blog post argues CIM covers power-system operations/planning/analysis but not buildings, foundations, protection-and-control artifacts, or drawings, and markets a branch-based concurrent-engineering approach layering IFC (building/geometry standard) alongside CIM — [Bentley blog](https://blog.bentley.com/software/why-your-substation-data-model-is-holding-you-back-and-what-to-do-about-it/). This is vendor marketing for Bentley's own tooling, not independent research, and should be cited as such.
- Verance AI markets a Neo4j-based CIM knowledge graph overlaying live SCADA telemetry, queryable via MCP-connected LLMs, and lists DNP3 and IEC 61850 among "supported protocols" — [veranceai.pages.dev](https://veranceai.pages.dev/). No independent evidence, benchmark, or published architecture accompanies this claim; treat purely as a vendor's marketing claim, not evidence that IEC 61850/SCL has actually been modeled in their graph.
- A public engineering-discussion wiki page (Statnett's open-source `Talk2PowerSystem` project), authored by a named Siemens consultant (Deniz Raif Durmaz) as a personal competency-questions contribution, states: "no single database technology can optimally serve all query categories" — relational databases struggle with large graph-shaped topologies, triple stores lag on real-time state, and time-series databases lose structural context; he reports working with real-world CIM network models of ~40 million triples, and a prototype (built on Microsoft Orleans, not a conventional triple store) processing ~40M triples in roughly 8 seconds; he explicitly states that SCADA and IEC 61850 substation-automation queries need data beyond what a CIM semantic/triple-store layer alone holds — [GitHub wiki](https://github.com/statnett/Talk2PowerSystem/wiki/Demo8-Deniz-Raif-Durmaz). This is a single contributor's personal architectural opinion and prototype result on a public wiki, not a published/peer-reviewed benchmark or Statnett's confirmed production architecture — cite it as such.

#### Inferences
- The strongest, most load-bearing citable fact for a final report's "limitations/risks" section is the Statnett wiki's point that heterogeneous query needs (static topology, real-time state, time-series history) typically can't be served well by one database technology alone — this directly supports a recommendation that an SCL knowledge graph should be scoped as "configuration/topology/dependency" tooling, not conflated with real-time SCADA state storage or historian functions.
- The 40M-triple / ~8-second figure is a single prototype data point on non-standard infrastructure (Orleans), not a benchmark of any named triple store (GraphDB, Jena, RDFox) or property-graph product, and should not be generalized into a scale claim for either technology family without a caveat.
- Marketing material (Bentley, Verance AI) should not be cited in a final report as evidence that IEC 61850/SCL-to-graph is a solved, productized problem; it only establishes that vendors perceive commercial demand for "substation + graph + AI" positioning.

#### Gaps
- No independent, peer-reviewed benchmark comparing a property-graph database and an RDF triple store specifically on IEC 61850 SCD-scale data (thousands of LNs, dozens of IEDs) was found. The general property-graph-vs-RDF performance claims in Part B's comparison section are therefore sourced from general graph-technology comparison write-ups (vendor blogs, consultancy white papers), not from substation-specific benchmarks — this is flagged again in Part B.
- Full text of the EMIE 2022 digital-twin paper was not retrieved (listing/abstract only); its graph-database architecture details beyond "used to organize module connections" are unconfirmed.

---

## Part B — Reasoned Proposal (Author's Own Analysis, Not Established Prior Art)

Everything below is **original analysis produced for this research task**, informed by the IEC 61850-6 (SCL) standard's own published structure and general graph-database/RDF literature, not a reproduction of an existing, citable industry schema. No prior-art source in Part A publishes a complete node/edge schema, example-query set, or ingestion-pipeline design for SCL specifically — this section fills that gap with a defensible, clearly-labeled proposal. Where a design choice is grounded in a cited general-graph-modeling or CIM/RDF source, the citation is given; where it is simply domain reasoning from SCL's own structure, it is marked **(proposal)**.

### B.1 Node-type schema (proposal)

SCL's own hierarchy (Substation section; IED section; Communication section; DataTypeTemplates section) maps naturally onto two different concerns that are worth keeping as **separate node families** rather than one undifferentiated tree, because they answer different classes of engineering question: (1) the **physical/functional topology** (substation plant structure, IEDs, their logical architecture) and (2) the **type system** (LNodeType/DOType/DAType/EnumType templates that physical instances reference). Conflating instance and type nodes makes "what does this LN actually expose" queries awkward; keeping them separate and linked by explicit `INSTANCE_OF`/`TYPED_AS` edges mirrors how SCL itself separates the `<Substation>`/`<IED>` sections from `<DataTypeTemplates>`.

| Node label | Derived from SCL element(s) | Suggested node **properties** (scalar, low-cardinality, rarely queried as their own entity) | Modeled as separate nodes/edges instead, and why |
|---|---|---|---|
| `Substation` | `<Substation>` | `name`, `desc` | — |
| `VoltageLevel` | `<VoltageLevel>` | `name`, `desc`, `nomFreq`, `numPhases`, voltage value+unit/multiplier | — |
| `Bay` | `<Bay>` | `name`, `desc` | — |
| `ConductingEquipment` | `<ConductingEquipment>` | `name`, `type` (CBR/DIS/CTR/VTR/etc.), `desc` | Terminal connectivity (`<Terminal>` with `connectivityNode`) → separate `ConnectivityNode` nodes + `CONNECTED_TO` edges, since connectivity is itself a graph, not a scalar attribute |
| `IED` | `<IED>` | `name`, `manufacturer`, `type`, `configVersion`, `originalSclVersion/Revision`, `desc` | — |
| `AccessPoint` | `<AccessPoint>` under `<IED>` | `name`, `desc`, `router` flag, `clock` flag | — |
| `Server` | `<Server>` under `<AccessPoint>` | `desc` | — |
| `LDevice` | `<LDevice>` under `<Server>` | `inst`, `desc`, `ldName` (computed) | — |
| `LN0` / `LogicalNode` | `<LN0>`, `<LN>` under `<LDevice>` | `lnClass`, `inst`, `prefix`, `lnType` (kept as a property **and** materialized as an edge, see below), `desc` | — |
| `DataObject` (DO/DOI) | `<DOI>` instance under LN, and the `<DO>` declaration inside an `LNodeType` | `name`, `desc`; **instance-level** `SDI`/`DAI` value overrides as properties only if scalar and low-cardinality | Nested `SDI` (sub-data-object) structures → child `DataObject` nodes with `CONTAINS` edges, since SCL allows arbitrary nesting depth |
| `DataAttribute` (DA/DAI) | `<DAI>` instance, `<DA>`/`<BDA>` declaration inside a `DOType`/`DAType` | `name`, `fc` (functional constraint), `bType`, `valKind`, `val` (the actual configured value, when present) | — |
| `LNodeType` | `<LNodeType>` in `DataTypeTemplates` | `id`, `lnClass`, `desc` | `<DO>` children → `DataObject`-template nodes + `HAS_DO` edges |
| `DOType` | `<DOType>` | `id`, `cdc` (common data class), `desc` | `<DA>`/`<SDO>` children → `DataAttribute`/`DataObject`-template nodes + edges |
| `DAType` | `<DAType>` | `id`, `desc` | `<BDA>` children → nested `DataAttribute`-template nodes |
| `EnumType` | `<EnumType>` | `id`, `desc` | `<EnumVal>` entries → `EnumValue` nodes (ord + literal) if enumerations are large/queried, else a JSON/array property for small enumerations **(proposal, pragmatic cutoff)** |
| `SubNetwork` | `<SubNetwork>` in `<Communication>` | `name`, `type` (e.g., "8-MMS", "IEC 61850-9-2 SV"), `desc` | — |
| `ConnectedAP` | `<ConnectedAP>` in `<Communication>` | `iedName`, `apName`; IP/MAC/VLAN addressing (`<Address>` P-elements: IP, IP-SUBNET, IP-GATEWAY, OSI-AP-Title, etc.) — **store address P-elements as properties on ConnectedAP** since they are a fixed, small, well-known set and are the main target of "find IPs" queries | GOOSE/SMV subscription endpoints (`<GSE>`, `<SMV>` with `ldInst`/`cbName`) → modeled via edges to `GSEControl`/`SampledValueControl`, not as scalar properties, because they are *references*, not attributes |
| `DataSet` | `<DataSet>` under `LN0`/`LN` | `name`, `desc` | `<FCDA>` members → separate `FCDA` nodes (see edges) rather than a property list, because FCDAs are themselves referenced/counted (e.g., "empty dataset" queries) |
| `FCDA` | `<FCDA>` | `ldInst`, `prefix`, `lnClass`, `lnInst`, `doName`, `daName`, `fc` | — |
| `GSEControl` | `<GSEControl>` under `LN0` | `name`, `appID`, `confRev`, `type` (GOOSE), `desc` | Linked `<GSE>` communication parameters (MAC, VLAN-ID, VLAN-PRIORITY, MinTime/MaxTime) → properties on the edge to `SubNetwork`/`ConnectedAP` or on a thin `GSE` node, since they are communication-layer config, not LN-layer config **(proposal)** |
| `SampledValueControl` | `<SampledValueControl>` under `LN0` | `name`, `smvID`, `confRev`, `smpRate`, `nofASDU`, `desc` | — |
| `ReportControl` | `<ReportControl>` under LN | `name`, `confRev`, `buffered` flag, `bufTime`, `intgPd`, `rptID` | `<TrgOps>`, `<OptFields>` → small property sets (bitmask-like), fine as scalar properties **(proposal)** |
| `Inputs` / `ExtRef` | `<Inputs>`/`<ExtRef>` under an LN | `intAddr`, `desc` | The actual subscription target (`iedName`, `ldInst`, `prefix`, `lnClass`, `lnInst`, `doName`, `daName`, or `serviceType`+`srcLDInst`+`srcCBName` for signal-based ExtRef) → modeled as a `SUBSCRIBES_TO` edge resolved at ingestion time to a concrete remote `DataAttribute`/`DataObject`/`GSEControl`/`SampledValueControl` node (see B.2), not left as unresolved string properties, because resolving it is precisely what makes the graph valuable over the raw XML |

**Design principle used throughout (proposal):** a field becomes a **graph edge/node** rather than a **flat property** whenever (a) SCL itself expresses it as a reference to another named element (type names, `ExtRef` tuples, `cbName`/control-block references, `connectivityNode`), or (b) the field is something an engineer will want to traverse, count, filter-via-join, or aggregate across many parents (dataset membership, LN type conformance, subscription fan-in/fan-out). Everything else (simple descriptive/config scalars with no cross-reference semantics) stays a property for both property-graph and RDF cases — this is standard graph-modeling guidance, not SCL-specific, and is consistent with general "when to use a relationship vs. a property" advice found in mainstream graph-database modeling literature (not independently re-cited here beyond the general property-graph-vs-RDF sources in Part A/Key Question 3).

### B.2 Edge-type schema (proposal)

| Edge | Direction | Source in SCL | Notes |
|---|---|---|---|
| `CONTAINS` | `Substation → VoltageLevel → Bay → ConductingEquipment` | nesting in `<Substation>` | Plain containment hierarchy |
| `CONTAINS` | `IED → AccessPoint → Server → LDevice → LN0/LN` | nesting in `<IED>` | Plain containment hierarchy |
| `CONTAINS` | `LN → DataObject → DataAttribute` (and nested `DataObject → DataObject` for SDI nesting) | `<DOI>/<SDI>/<DAI>` nesting | Instance-side containment |
| `CONTAINS` | `LNodeType → DataObject(template) → DataAttribute(template)`, `DOType → DA/SDO`, `DAType → BDA` | `DataTypeTemplates` nesting | Type-side containment — kept as a **parallel but distinct** containment tree from the instance side |
| `INSTANCE_OF` | `LN → LNodeType` | `LN/@lnType` → `LNodeType/@id` | Resolved at ingestion (string match); this is the single most important integrity-check edge — a dangling `lnType` reference is a real-world data-quality defect to detect |
| `TYPED_AS` | `DataObject → DOType`, `DataAttribute → DAType`, `DataAttribute → EnumType` | `@type` attributes inside type templates | Same resolution/integrity concern as above |
| `ASSOCIATED_WITH` | `LNode (in Substation section) → ConductingEquipment` | `<LNode>` element under a bay/equipment, `iedName`+`ldInst`+`prefix`+`lnClass`+`lnInst` | This is SCL's *own* built-in cross-reference between substation topology and IED logical nodes — arguably the most "native" graph edge already present in the standard |
| `HAS_MEMBER` | `DataSet → FCDA` | `<FCDA>` children of `<DataSet>` | — |
| `REFERENCES` | `FCDA → DataAttribute` (or `DataObject` when `fc`/`daName` absent, i.e., whole-DO FCDA) | `FCDA` fields resolved against the owning LN's `DOI/DAI` instance tree (or, if absent, against the LN's `LNodeType→DOType→DA` template) | Needs the `INSTANCE_OF`/`TYPED_AS` resolution to already exist, since an FCDA frequently references a *type-level* DA rather than an explicit instance override |
| `PUBLISHES` | `GSEControl/SampledValueControl/ReportControl → DataSet` | `@datSet` attribute | A control block with no resolvable `datSet`, or whose dataset resolves to zero `HAS_MEMBER` edges, is the "empty/misconfigured ReportControl" defect class called out in the task's example queries |
| `SUBSCRIBES_TO` | `Inputs/ExtRef (on a subscriber LN) → DataAttribute/DataObject` (value-based ExtRef) or `→ GSEControl/SampledValueControl` (control-block/service-based ExtRef, i.e. `serviceType="GOOSE"` with `srcLDInst`+`srcCBName`) | `<ExtRef>` fields matched against the *publishing* IED's resolved model | This is the cross-IED data-flow edge and is almost always the hardest to resolve correctly, because `ExtRef/@iedName` must match another `IED/@name` **elsewhere in the same SCD**, and because Edition 1 vs Edition 2 ExtRef attribute sets differ |
| `CONNECTED_VIA` | `IED → AccessPoint` | containment, restated as a named edge for query ergonomic reasons | **(proposal)**: duplicating a containment edge under a more query-friendly name is a judgment call, not a necessity — could equally be left as plain `CONTAINS` |
| `ON` | `ConnectedAP → SubNetwork` (and, by extension, `AccessPoint ... ON ... SubNetwork` via the `ConnectedAP` join) | `<ConnectedAP>` nesting under `<SubNetwork>` in `<Communication>`, matched back to the `IED/AccessPoint` it names | This is the key "which IEDs share a SubNetwork" edge |
| `CONNECTED_TO` | `ConductingEquipment ↔ ConductingEquipment` (via shared `ConnectivityNode`) | `<Terminal>/@connectivityNode` | Electrical topology graph; optional depending on whether electrical (not just IED/communication) topology is in scope |

### B.3 Property-graph vs RDF/OWL — comparison grounded in the SCL use case

This comparison intentionally avoids generic "graph databases are fast" marketing claims (several of which surfaced in the Key-Question-3 search and are explicitly vendor-sourced — see Part A) and instead reasons through each criterion against SCL's actual shape and the kinds of questions listed in the task.

**Schema flexibility.** SCL is semi-structured but has a genuinely open extension point: `<Private>` elements can appear at almost any level and carry vendor-specific, arbitrarily-shaped content, and IEDs frequently differ edition-to-edition (Ed1 vs Ed2.1 ExtRef attributes, the Ed2.1-only `<Line>`/`<Process>` elements noted in the SCL background search). A labeled-property-graph (LPG) model tolerates this well: a node can simply carry extra, unmodeled properties or a `Private` sub-node with a loosely-typed payload, and nothing else in the graph needs to change. An RDF/OWL model *can* also tolerate open-world extension (that is RDF's whole design point — triples about a resource can come from anywhere, and OWL is open-world by default), but doing so cleanly still requires deciding on a predicate/class for the private content, which in practice means either (a) a generic `scl:hasPrivateContent` literal-blob predicate (which gives up queryability, matching the LPG "extra property" approach) or (b) a growing set of vendor-specific sub-ontologies (closer to how CIM profiles proliferate). Neither family gets this "for free" from SCL; LPG's lower schema ceremony makes the pragmatic path shorter.

**Standardization / interoperability value.** This is the one criterion where the Part A prior art directly matters: CIM already has a mature, standardized RDF/OWL/SHACL ecosystem in production at ENTSO-E (CGMES), and the IEC TC57 CIM–61850 harmonization effort (TS 62361-102, proposed 62361-105) is explicitly aimed at a common UML model spanning both standards. *If* an organization's long-term goal includes joining SCL-derived data with CIM-derived grid-model data (e.g., linking an `XCBR` logical node back to its CIM `Breaker` asset for asset-management or outage-analysis purposes), choosing RDF/OWL for the SCL graph has a real, citable interoperability argument behind it: the destination ecosystem CIM already lives in is RDF. If the goal is purely internal (engineering impact analysis, configuration QA, documentation for one organization's own IEC-61850 fleet), this advantage is mostly theoretical, since — per Part A, Key Question 1 — no finished, ratified ontology exists that already does the SCL-to-CIM-RDF mapping; a team would still be doing the Santodomingo/Uslar/Rohjans-style manual alignment work either way.

**Query ergonomics for the task's example questions.** Most of the questions given in the task ("which IEDs subscribe to GOOSE from IED X," "full data flow from PTOC.Op to the tripped breaker," "all XCBR LNs and their parent Bay," "empty ReportControl blocks," "IEDs on SubNetwork Y and their IPs") are **variable-length or fixed-depth path traversals with filtering on node labels/properties along the way** — exactly the pattern Cypher's `MATCH (a)-[:REL*]->(b) WHERE ...` syntax is designed to express tersely. The same questions are answerable in SPARQL via property paths (`?a scl:subscribesTo+ ?b`) and are not fundamentally harder to answer *once the data is loaded and the right predicates exist* — but the query text is usually more verbose because every edge traversal is a triple pattern with an explicit variable, and the lack of a native "node label with multiple properties in one line" syntax (everything is a triple) means SCL's many-attribute nodes (e.g., `ConnectedAP` with 5–6 address P-elements) produce noticeably longer SPARQL than the equivalent Cypher. This is a query-ergonomics observation grounded in the two languages' own design (property paths exist in SPARQL 1.1; Cypher's pattern syntax is node/relationship-centric), not a claim sourced from a specific SCL benchmark — none was found in Part A.

**Tooling maturity.** Both sides have mature options, but maturity is shaped differently for this use case. Neo4j/Cypher and Memgraph have strong, well-documented XML/CSV bulk-import tooling and APOC-style procedural extensions useful for a custom SCL parser's output; Amazon Neptune supports property-graph (via openCypher/Gremlin) with managed-service operational maturity. On the RDF side, Apache Jena/Fuseki and Ontotext GraphDB have mature SHACL validation support, which is directly useful for *semantic* validation of SCL-derived data (e.g., "every `ReportControl.datSet` must resolve to an existing `DataSet`" is a natural SHACL shape), and RDFox adds materialized/incremental reasoning at speed. Neither family has IEC-61850-specific tooling maturity (no vendor was found, in Part A, shipping a ready SCL-to-graph loader for either paradigm) — so "maturity" here really means "maturity of the generic platform," and a project will be writing its own SCL ingestion/mapping layer regardless of which family is chosen.

**Performance at scale (thousands of LNs across dozens of IEDs).** A large SCD (dozens of IEDs × tens of LNs each × several DOs/DAs each) is on the order of 10³–10⁵ nodes and a similar-to-somewhat-larger edge count once DO/DA/type-template nodes are included — small by either technology's standards; the Statnett-wiki data point (Part A, Key Question 3) of ~40 million CIM triples processed in ~8 seconds on a custom (non-standard) prototype suggests that scale concerns are unlikely to be the deciding factor for a single SCD/ICD-derived graph at this size, in either paradigm. The more realistic scale concern is **ingesting and re-resolving many SCDs together** (e.g., a fleet of substations) or keeping **historical configRev-versioned snapshots** (Part C below) — which is primarily a data-management/versioning design question, not a raw query-engine throughput question, for data of this size.

**Inference/reasoning.** This is the clearest asymmetry. OWL reasoning (and, more lightweight, SHACL validation) gives a direct, standards-based way to express and automatically check statements such as "an LN of class `XCBR` must expose a `Pos` data object of CDC `DPC`" (i.e., LN-class conformance to IEC 61850-7-3/7-4 common data classes) as a reusable ontology-level constraint, checked once and applied to every instance — this is exactly the kind of rule IEC 61850's own 7-x part documents define declaratively as "LN class X shall have mandatory DO Y of CDC Z," which maps naturally onto OWL class restrictions or SHACL shapes. A property-graph database has no native equivalent; the same conformance check must be hand-written as a traversal/validation query or external script re-run against the graph, which is operationally equivalent in effect but not declarative/reusable in the same standards-based way. This reasoning advantage is the strongest technical (not just interoperability) argument for RDF/OWL in this specific use case, and it is grounded in how IEC 61850-7-x itself already expresses LN-class/CDC conformance rules, not in generic "OWL is good at reasoning" marketing.

**Overall judgment (proposal, not a citable consensus):** for an organization whose primary near-term goal is engineering impact-analysis and configuration QA tooling for its own IEC 61850 fleet, a property graph (Cypher-family) is the pragmatic default — faster to stand up, better ergonomics for the dominant query pattern (path traversal with filtering), and no worse at handling SCL's `<Private>`-driven schema looseness. If the organization already has, or plans, a CIM/CGMES-based enterprise data layer and wants SCL data to join that world, or if automatic LN-class/CDC conformance checking is a first-class requirement, RDF/OWL (ideally tracking the IEC TC57 harmonization direction rather than inventing a parallel ontology) is the better-grounded choice, accepting the added SPARQL verbosity and ontology-engineering overhead. A hybrid is also a legitimate, commonly-cited pattern in general graph literature (property graph for day-to-day traversal/analytics, RDF/OWL overlay or periodic export for standards-based reasoning/interoperability) — see the general property-graph-vs-RDF sources in Part A, Key Question 3 — though no source there demonstrates this specifically for SCL.

### B.4 Example queries (proposal — schema from B.1/B.2)

**1. Which IEDs subscribe to GOOSE messages published by IED X?**

Cypher:
```
MATCH (pubIed:IED {name:"X"})-[:CONTAINS*]->(:LN0)-[:PUBLISHES]->(gc:GSEControl)
MATCH (subIed:IED)-[:CONTAINS*]->(:LN)-[:SUBSCRIBES_TO]->(gc)
RETURN DISTINCT subIed.name
```

SPARQL:
```sparql
PREFIX scl: <http://example.org/scl#>
SELECT DISTINCT ?subIedName WHERE {
  ?pubIed a scl:IED ; scl:name "X" ; scl:contains+ ?ln0 .
  ?ln0 a scl:LN0 ; scl:publishes ?gc .
  ?gc a scl:GSEControl .
  ?subIed a scl:IED ; scl:contains+ ?ln .
  ?ln a scl:LN ; scl:subscribesTo ?gc .
  ?subIed scl:name ?subIedName .
}
```

**2. Full data flow from a protection trip signal (PTOC.Op) to the breaker that trips.**

Cypher:
```
MATCH (ptoc:LN {lnClass:"PTOC"})-[:CONTAINS]->(op:DataObject {name:"Op"})
MATCH (fcda:FCDA)-[:REFERENCES]->(op)
MATCH (ds:DataSet)-[:HAS_MEMBER]->(fcda)
MATCH (gc:GSEControl)-[:PUBLISHES]->(ds)
MATCH (xcbrLN:LN)-[:SUBSCRIBES_TO]->(gc)
MATCH (xcbrLN)-[:CONTAINS*0..]->(ctlDO:DataObject)   // e.g. a Pos/SPCSO control DO on the receiving XCBR
WHERE xcbrLN.lnClass = "XCBR"
MATCH (lnode:LNode)-[:ASSOCIATED_WITH]->(cb:ConductingEquipment {type:"CBR"})
WHERE lnode.lnClass = "XCBR"  // and the same IED/LDevice/inst as xcbrLN, matched in practice via its resolved reference
RETURN ptoc, op, fcda, ds, gc, xcbrLN, cb
```
*(Note — proposal caveat: matching the subscribing `XCBR` LN instance back to its substation-topology `LNode`/`ConductingEquipment` requires that the `LNode` cross-reference's `iedName`/`ldInst`/`prefix`/`lnInst` tuple be joined against the same tuple on the LN reached via `SUBSCRIBES_TO`, which is straightforward at ingestion time but is simplified/omitted above for readability.)*

SPARQL:
```sparql
SELECT ?ptoc ?fcda ?dataset ?gseControl ?xcbrLN ?breaker WHERE {
  ?ptoc a scl:LN ; scl:lnClass "PTOC" ; scl:contains ?op .
  ?op scl:name "Op" .
  ?fcda scl:references ?op .
  ?dataset scl:hasMember ?fcda .
  ?gseControl scl:publishes ?dataset .
  ?xcbrLN scl:subscribesTo ?gseControl ; scl:lnClass "XCBR" .
  ?lnode scl:associatedWith ?breaker .
  ?breaker a scl:ConductingEquipment ; scl:type "CBR" .
  ?lnode scl:lnClass "XCBR" .
}
```

**3. List all logical nodes of class XCBR and their parent Bay.**

Cypher:
```
MATCH (lnode:LNode {lnClass:"XCBR"})-[:ASSOCIATED_WITH]->(:ConductingEquipment)<-[:CONTAINS]-(bay:Bay)
RETURN lnode, bay.name
```

SPARQL:
```sparql
SELECT ?lnode ?bayName WHERE {
  ?lnode a scl:LNode ; scl:lnClass "XCBR" ; scl:associatedWith ?ce .
  ?bay scl:contains ?ce ; scl:name ?bayName .
}
```

**4. Find all ReportControl blocks with no DataSet members (empty/misconfigured).**

Cypher:
```
MATCH (rc:ReportControl)
OPTIONAL MATCH (rc)-[:PUBLISHES]->(ds:DataSet)
OPTIONAL MATCH (ds)-[:HAS_MEMBER]->(fcda:FCDA)
WITH rc, ds, count(fcda) AS memberCount
WHERE ds IS NULL OR memberCount = 0
RETURN rc.name, ds.name, memberCount
```

SPARQL:
```sparql
SELECT ?rcName ?dsName (COUNT(?fcda) AS ?memberCount) WHERE {
  ?rc a scl:ReportControl ; scl:name ?rcName .
  OPTIONAL {
    ?rc scl:publishes ?ds .
    ?ds scl:name ?dsName .
    OPTIONAL { ?ds scl:hasMember ?fcda }
  }
}
GROUP BY ?rcName ?dsName
HAVING (!BOUND(?dsName) || COUNT(?fcda) = 0)
```

**5. Find all IEDs on SubNetwork Y and their IP addresses.**

Cypher:
```
MATCH (sn:SubNetwork {name:"Y"})<-[:ON]-(cap:ConnectedAP)
MATCH (ied:IED {name: cap.iedName})
RETURN ied.name, cap.ipAddr, cap.ipSubnet, cap.ipGateway
```

SPARQL:
```sparql
SELECT ?iedName ?ip ?subnet ?gateway WHERE {
  ?sn a scl:SubNetwork ; scl:name "Y" .
  ?cap scl:on ?sn ; scl:iedName ?iedName ;
       scl:ipAddr ?ip ; scl:ipSubnet ?subnet ; scl:ipGateway ?gateway .
}
```

### B.5 Ingestion pipeline (proposal)

1. **Parse.** XML-parse the SCD/ICD/SSD against the IEC 61850-6 XSD (edition-aware: Ed1 vs Ed2.0 vs Ed2.1 schemas differ, per the SCL background material in Part A — e.g., `<Line>`/`<Process>` only exist from Ed2.1). Reject or edition-tag non-conformant files at this stage.
2. **Validate — schema level.** XSD validation catches structural malformedness. This does **not** catch semantic errors (dangling type references, unresolved ExtRef targets, duplicate IPs) — those require a second pass.
3. **Validate — semantic level.** Walk the parsed tree and check: every `LN/@lnType` resolves to an existing `LNodeType/@id` (and transitively every `DO/@type`, `DA/@type` resolve); every `ExtRef/@iedName` resolves to another `IED/@name` in the same SCD; every control-block `@datSet` resolves to an existing `DataSet`; every `ConnectedAP` address block has no duplicate IP/MAC within the same SubNetwork. **(proposal)** This is the natural place to produce a structured "data-quality report" (dangling refs, duplicate IPs, empty datasets) *before* loading, so the graph is not silently populated with broken edges that "look" authoritative later (see Part B.7, Risks).
4. **Resolve references.** Materialize the edges in B.2 that require cross-element lookup: `INSTANCE_OF`/`TYPED_AS` (type templates), `PUBLISHES` (control block → dataset), `SUBSCRIBES_TO` (ExtRef → remote DA/DO or remote control block — this is the pass that turns isolated per-IED trees into a single cross-IED graph), `ASSOCIATED_WITH` (LNode → ConductingEquipment), `ON`/`CONNECTED_VIA` (ConnectedAP → SubNetwork → IED). This step is where edition differences in ExtRef attributes (Ed1 value-based vs Ed2 service-based subscriptions, e.g. `serviceType="GOOSE"` with `srcLDInst`/`srcCBName`) must be branch-handled explicitly.
5. **Load.**
   - **Batch (full reload):** simplest correctness story — parse+validate+resolve the whole SCD, then bulk-load into a fresh graph (or a new versioned sub-graph/named-graph), and cut over. Appropriate whenever a new `configRev`/`Hitem` revision is published for the whole SCD, which in practice is often the operative unit of change for IEC 61850 (SCL files carry a `<Hitem>`/history and `Services`/`Header` revision info that can be used as the version key). **(proposal — leverages SCL's own `<Header>`/`Hitem` versioning, not an external invention.)**
   - **Incremental:** feasible per-IED (reload just the IED subtree whose ICD/configuration changed and re-resolve only the edges touching it — `INSTANCE_OF`/`TYPED_AS` within that IED, plus any `SUBSCRIBES_TO`/`ASSOCIATED_WITH` edges elsewhere in the graph that point *at* that IED's elements), but requires careful invalidation of edges that previously pointed into the replaced subtree. Property graphs' explicit node identity (and RDF named-graphs/quads) both support this; it's an engineering-complexity trade-off (incremental = faster updates, more edge-case bug surface) rather than a technology-determined choice.
6. **Versioning historical snapshots.** Use SCL's own `Header/@id` + `Header/@version`/`@revision` (and/or `Hitem` history entries) as the natural version key; store each ingested snapshot either as (a) a time-stamped, fully separate graph/named-graph per version (simplest for "diff two versions" queries, costliest in storage), or (b) a single graph with `validFrom`/`validTo` temporal properties on nodes/edges (more storage-efficient, harder to query "as of time T" correctly). **(proposal — this is standard temporal-graph-modeling practice applied to SCL's own version fields, not a documented SCL-specific pattern from Part A.)**

### B.6 Benefits (proposal, reasoning from the schema above)

- **Impact analysis.** "If I change/remove this LN/DataSet/IED, what breaks?" becomes a graph traversal (`SUBSCRIBES_TO`/`PUBLISHES`/`REFERENCES` reverse-walk) instead of manual cross-referencing across dozens of ICD/IID files by hand.
- **Cross-IED dependency tracing.** The `SUBSCRIBES_TO` edges are precisely the GOOSE/SV producer-consumer dependencies that are otherwise implicit in scattered `ExtRef` blocks; making them explicit, queryable edges is the core value proposition of the whole exercise.
- **Cybersecurity/attack-surface analysis via communication topology.** The `ON`/`CONNECTED_VIA`/`SUBNetwork` edges directly represent the network segmentation that GOOSE/SV-attack literature (Part A, Key Question 3) treats as the primary exposure surface ("an adversary on the substation LAN can attack GOOSE traffic" — [arXiv 2511.18748](https://www.arxiv.org/pdf/2511.18748)); a graph of which IEDs/control-blocks share a SubNetwork, and which LNs subscribe across IED boundaries, is a reasonable starting data layer for that kind of analysis, though **no source in Part A describes this specific graph being built for security-analysis purposes** — this benefit is inferred, not documented prior art.
- **Documentation generation.** Since the graph already encodes containment + type + dataflow, generating human-readable "what does this IED do and who talks to it" documentation is a straightforward graph-to-template operation.
- **Change management.** Comparing two ingested snapshots (B.5.6) node-by-node/edge-by-edge gives a structured diff (which LNs added/removed, which subscriptions changed) that is considerably more precise than an XML text diff of the underlying SCD.

### B.7 Limitations and risks (proposal)

**Limitations**
- **Schema rigidity vs. `<Private>` extensibility.** Any fixed node/edge schema (property-graph *or* RDF/OWL) will, by construction, not natively model arbitrary vendor `<Private>` payloads; at best it stores them as an opaque blob property/literal, losing queryability for that content — a structural limitation of modeling a standard that explicitly allows unstructured extension points.
- **Scale of very large SCDs.** Not a raw query-performance problem at typical single-substation scale (Part A/B.3), but ingestion-time reference resolution (B.5 step 4) grows in complexity, not just size, as cross-IED ExtRef counts grow — this is a pipeline-engineering concern more than a database-technology concern.
- **Keeping the graph in sync with the authoritative SCL file.** The graph is a derived artifact; the SCD/ICD file (or an engineering tool's own project format) remains authoritative. The 2019 arXiv finding (Part A) that a graph-backed one-line-diagram tool can drift out of sync with its source unless explicitly kept synchronized is a direct, citable precedent for this exact risk.

**Risks**
- **Data-quality issues propagating from source SCDs into a graph that "looks" authoritative.** Dangling `lnType`/`ExtRef` references, duplicate IPs, and similar real-world SCD defects (exactly what the B.5 step-3 semantic validation pass is designed to catch) will, if ingestion skips that validation, silently become either missing edges or (worse) **incorrectly-resolved** edges in the graph — and a polished, queryable graph interface tends to *look* more trustworthy than the raw XML it came from, which is precisely the hazard: engineers may trust a graph-derived answer without realizing it encodes an upstream misconfiguration. This is a reasoned risk assessment, not a documented incident from Part A's sources, but it follows directly from the data-quality classes (dangling refs, duplicate IPs) explicitly named in the task and from the general "garbage in, garbage out" nature of any derived index.
- **Security of exposing substation topology/network data in a queryable graph.** The same `SubNetwork`/`ConnectedAP`/IP-address data that makes the graph useful for legitimate impact and attack-surface analysis (B.6) is itself sensitive operational-technology topology information; a queryable graph service is a new access surface that did not exist when this information was locked inside individual engineering-tool project files, and the GOOSE/SV attack literature in Part A (Key Question 3) establishes that network-level access to this kind of substation information is already a documented attack vector — so the graph database and its query interface need to be treated as OT-sensitive infrastructure in its own right (access control, network placement, audit logging), not as a general-purpose internal wiki.

---

## Source list (all URLs cited above, for the report-writer's convenience)

- https://vde-verlag.de/proceedings-en/453194053.html
- https://www.offis.de/en/offis/publication/ontology-based-integration-of-the-heterogeneous-standards-iec-61970-and-61850.html
- https://offis.de/offis/publikation/a-use-case-for-ontology-evolution-and-interoperability-the-iec-utility-standards-reference-framework-62357.html
- https://irma-international.org/teaching-case/use-case-ontology-evolution-interoperability/38044
- https://www.igi-global.com/chapter/use-case-ontology-evolution-interoperability/69121
- https://www.buchfreund.de/de/autor/mathias-uslar
- https://unpaywall.org/10.1109%2FIECON.2015.7392317
- https://arxiv.org/pdf/1508.06435
- https://reference.globalspec.com/ref/4470004/iec-ts-61850-7-7-2018
- https://ceur-ws.org/Vol-4064/PD-paper1.pdf
- https://arxiv.org/pdf/2608.16001
- https://www.kth.se/epe/calendar/exjobb/automated-configuration-of-digital-substation-infrastructure-using-iec-61850-scl-files-1.1481537
- https://eepublicdownloads.entsoe.eu/clean-documents/CIM_documents/Grid_Model_CIM/RDF-SyntaxUserGuide_v_1-1-0.pdf
- https://opencgmes.soptim.de/reference/cgmes-background
- https://www.entsoe.eu/Documents/CIM_documents/Grid_Model_CIM/RDF-SyntaxUserGuide_v1-0.pdf
- https://docs.google.com/presentation/d/1ktXSCo3akYUnZH2ZKGs8CfpmnMWYtnui/htmlpresent
- https://www.e-cigre.org/publications/detail/d2-12614-2026-from-documents-to-knowledge-graphs-intelligent-requirements-management-using-cim-based-ontology.html
- https://webstore.iec.ch/publication/27417
- https://naspi.org/sites/default/files/reference_documents/cim_61850_harmonized_model_for_smart_grid.pdf
- https://www.pacw.org/?p=10456
- https://www.pacw.org/iec-tc-57-wg-17-update-13
- https://koreascience.kr/article/CFKO201133254116584.pdf
- https://iit.comillas.edu/publicacion/congreso/en/10897/Ontology%20matching%20approach%20to%20the%20harmonization%20of%20CIM%20and%20IEC%2061850%20standards
- https://iit.comillas.edu/publicacion/congreso/en/10978/Towards%20the%20automatic%20alignment%20of%20CIM%20and%20SCL%20ontologies
- https://www.iit.comillas.edu/documentacion/revista/IIT-13-065A_preview/Facilitating%20the%20automatic%20mapping%20of%20IEC%2061850%20signals%20and%20CIM%20measurements.pdf
- https://www.vde-verlag.de/proceedings-en/565961155.html
- https://ar5iv.labs.arxiv.org/html/1903.09495
- https://blog.bentley.com/software/why-your-substation-data-model-is-holding-you-back-and-what-to-do-about-it/
- https://veranceai.pages.dev/
- https://github.com/statnett/Talk2PowerSystem/wiki/Demo8-Deniz-Raif-Durmaz
- https://www.arxiv.org/pdf/2511.18748
