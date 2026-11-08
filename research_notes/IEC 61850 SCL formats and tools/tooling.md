# Note on plan mode

This agent was invoked (via the deep-research skill) with instructions to research IEC 61850 SCL tooling and save findings to:
`D:\Trivium-Inhouse\SCD-POC\research_notes\IEC 61850 SCL formats and tools\tooling.md`

However, the session is in **plan mode**, which restricts this agent to read-only actions and to editing only this plan file. The `Write` tool could not be used to create the requested deliverable file. All research was completed using read-only web search (WebSearch), and the full findings are captured below in the exact three-section-per-question format the deep-research skill expects. **Once plan mode is exited / approval is given, the content below should be written verbatim to the target path** (`D:\Trivium-Inhouse\SCD-POC\research_notes\IEC 61850 SCL formats and tools\tooling.md`).

---

# IEC 61850 SCL Tooling: Engineering, Viewing, Validation and Test Tools

## Q1: OMICRON IEDScout — what does it do, main features?

### Takeaway
IEDScout is OMICRON's universal IEC 61850 client/exploration and simulation tool: it connects to live IEDs over MMS, subscribes to and simulates GOOSE, can load/parse SCL (ICD/CID/SCD) files to explore or simulate a device's data model, and supports IEC 61400-25 in addition to IEC 61850. It is a live-device test/exploration tool first, with SCL-file support as an input/simulation mechanism rather than an SCL authoring tool.

### Cited Findings
- IEDScout acts as a universal MMS client to IEC 61850 servers, letting a user drill into lower protocol layers (MMS, Ethernet) and export those layers for traffic analysis — [pdf.directindustry.com brochure](https://pdf.directindustry.com/pdf/omicron-electronics/iedscout/13971-614616.html)
- It scans the network for GOOSE messages, presents them for subscription, can record GOOSE sequences in COMTRADE format (since live GOOSE traffic runs too fast to trace manually), and can simulate GOOSE messages — [pdf.directindustry.com brochure](https://pdf.directindustry.com/pdf/omicron-electronics/iedscout/13971-614616.html); [tdworld.com — Analyzing IEC 61850 SCADA Communication](https://www.tdworld.com/test-and-measurement/article/20962970/analyzing-iec-61850-scada-communication)
- Version 3 combines client/server and GOOSE communication into one unified event list — [tdworld.com](https://www.tdworld.com/test-and-measurement/article/20962970/analyzing-iec-61850-scada-communication)
- SCL files or discovered live IEDs can both be used as the basis for simulating whole IEDs (server, Reports, GOOSE) — [tdworld.com — Simulating IEC 61850 IEDs](https://www.tdworld.com/test-and-measurement/simulating-iec-61850-ieds); OMICRON Test Universe collateral describing IEDScout's SCL parser — [pacw.org — Test Universe 4.30](https://www.pacw.org/test-universe-4-30)
- IEDScout includes "an intelligent and powerful SCL parser to check the quality of the engineering files according to IEC 61850-6" — [pacw.org — Test Universe 4.30](https://www.pacw.org/test-universe-4-30)
- Dragging data points to an "Activity Monitor" starts polling a value, subscribing to a GOOSE, or enabling a report — [electricalreview.co.uk — Intelligent IEC61850 testing](https://electricalreview.co.uk/?p=52414)
- It supports IEC 61400-25 (wind turbine communications) in addition to IEC 61850 editions — [tdworld.com](https://www.tdworld.com/test-and-measurement/article/20962970/analyzing-iec-61850-scada-communication)

### Inferences
- IEDScout sits in the "live device testing/exploration" category rather than the "SCL authoring" category: its SCL handling is about reading/validating/simulating from an SCL file, not about producing or editing one for a project.
- Because it is bundled with/related to OMICRON Test Universe (the same vendor's conformance/functional test platform), IEDScout functions as a companion exploration tool to a broader test suite rather than a standalone system engineering tool.

### Gaps
- Could not confirm from available sources the exact SCL schema editions (Ed1/Ed2/Ed2.1) IEDScout's parser supports, or whether it can author/export SCL files (modify and save back to ICD/CID) versus read-only parsing.
- Version-specific feature differences (2.0 through 5.00) were not fully reconciled; the most recent version's full changelog was not found in search results.

---

## Q2: SCD explorers/viewers generically, and named tools (Helinks STS, "IEC 61850 Explorer", vendor SCTs, open-source tools)

### Takeaway
"SCD explorer/viewer" is not a single product category but spans (a) vendor System Configuration Tools (SCTs) that author/edit SCD files for a whole substation (Helinks STS, Siemens IEC 61850 System Configurator/DIGSI 5, ABB/Hitachi Energy IET600), (b) IED-level configuration tools that import/export ICD/CID (SEL AcSELerator Architect, GE EnerVista UR Setup/3 Series/Viewpoint Engineer), (c) lightweight viewers/parsers (SCL Navigator, legacy IEDExplorer, ASE Visual SCL), and (d) open-source browser-based editors (OpenSCD and its CoMPAS fork). No tool was found in search results literally named "IEC 61850 Explorer"; the closest matches are IEDExplorer (open-source, MMS client + SCL parser) and vendor tools with "Explorer" in the name (Hitachi Energy ITT600 SA Explorer — a live diagnostic tool, not primarily an SCL viewer).

### Cited Findings

**Helinks STS (Triangle MicroWorks / Helinks)**
- Designed for top-down, device-independent engineering per IEC 61850 parts 4 and 6; capabilities include SCL import/export, direct SCL editing and validation, signal engineering, and automatic generation of MMS report and GOOSE communication configuration — [dtpartners.com.au](https://dtpartners.com.au/?p=3110)
- Includes graphical editors for single-line, function, and system diagrams — [Triangle MicroWorks — Helinks STS overview](https://products.trianglemicroworks.com/products/testing-and-configuration-tools/helinks-pages/overview)
- Supports Edition 1 and Edition 2 of IEC 61850 — [helinks.com](https://helinks.com)
- Can import any SCL file type including ICD and SCD — [Helinks STS Components and Concepts](https://docs.helinks.com/userdoc/3.14/helinks-sts-components-and-concepts)
- Supports Excel import/export of signal lists — [helinks.com/index.php/sts](https://helinks.com/index.php/sts/)
- Vendor-specific "packages" are needed to generate SCD communication configuration for particular vendors' IEDs — [dtpartners.com.au](https://dtpartners.com.au/?p=3110)

**"IEC 61850 Explorer" (no exact-name match found)**
- IEDExplorer (SourceForge, open source): an IEC 61850 MMS client for testing/educational purposes; a variant "IEDExplorer w/ XML Parse" adds an SCL XML parser — [sourceforge.net/p/iedexplorer](https://sourceforge.net/p/iedexplorer/wiki/Home/); [sourceforge.net/projects/iedexplorerwxmlparse](https://sourceforge.net/projects/iedexplorerwxmlparse/)
- Hitachi Energy ITT600 SA Explorer: described as "an integrated testing tool for diagnosis and troubleshooting of IEC-61850-compliant substation automation systems" — a live diagnostic client, not an SCL file viewer per se — [Hitachi Energy — ITT600 SA Explorer release notes](https://www.hitachienergy.com/me/en/news-and-events/product-releases/2023/12/release-of-itt600-sa-explorer-version-2-1-service-pack-3)
- ASE "Visual SCL": an older graphical tool for creating, editing and viewing IEC 61850 SCL files — [blog.nettedautomation.com (2008)](https://blog.nettedautomation.com/2008/07/did-you-know-visual-scl.html)

**Siemens IEC 61850 System Configurator (bundled in DIGSI 5 Standard)**
- Described by Siemens as a "manufacturer-neutral solution for interoperable engineering of all IEC 61850 products, including devices from third parties" — [via scribd copy of Siemens application note](https://www.scribd.com/document/332121696/Sys-Con-Help)
- Imports/exports all SCL file types from IEC 61850-6: ICD, IID, CID, SCD, SSD, SED — [reliservsolutions.tradeindia.com product listing](https://reliservsolutions.tradeindia.com/siemens-iec-61850-system-configurator-engineering-software-for-iec-61850-systems-6873370.html)
- Bundled only with DIGSI 5 Standard (not Compact); Compact limits a project to one SIPROTEC 5 device and lacks the system configurator — [reliservsolutions.tradeindia.com](https://reliservsolutions.tradeindia.com/digsi-5-4356400.html)
- Workflow: devices added to a station as ICD/IID/SCD files; two main views are "Network" and "Connection"; resulting SCD can be imported into other software (e.g., SICAM PAS) — [Siemens SysConHelp manual (scribd copy), V5.90](https://cache.industry.siemens.com/dl/files/201/109770201/att_994358/v1/SysConHelp_en.pdf)
- Manual's main topics: station work, export/import, IED log collection, firmware upload, printing — [Siemens SysConHelp manual](https://cache.industry.siemens.com/dl/files/201/109770201/att_994358/v1/SysConHelp_en.pdf)

**ABB / Hitachi Energy IET600 (Integrated Engineering Tool)**
- Engineering tool for designing/configuring system-wide IEC 61850 communication dataflow between IEDs via graphical editors for substation topology and physical communication infrastructure — [ABB webinar, 2015](https://library.e.abb.com/public/0c3ca16492c542d8b9663ab8e2c35488/2015%20Simulation%20and%20Testing%20Methodologies_Self.pdf)
- The complete system is documented in a standards-compliant, reusable SCD file supporting multi-vendor integration — [ABB webinar, 2015](https://library.e.abb.com/public/0c3ca16492c542d8b9663ab8e2c35488/2015%20Simulation%20and%20Testing%20Methodologies_Self.pdf)
- SCD/CID import, or manual creation, of datasets, report control blocks, GOOSE control blocks and sampled value control blocks — [ABB webinar, 2015](https://library.e.abb.com/public/0c3ca16492c542d8b9663ab8e2c35488/2015%20Simulation%20and%20Testing%20Methodologies_Self.pdf)
- A formal SCL Implementation Conformance Statement exists for IET600 v5.3 covering mandatory/optional SCT features including SCD header revision handling and mandatory SCD export — [ABB SICS PDF](https://library.e.abb.com/public/bd354523bcbb4458be241235c6f053df/1KHL504752%20IET600%20SICS%20Implementation%20Conformance%20Statement.pdf)
- Later releases add: reading signed SCL files per IEC 62351, engineering of IEC 61869-9 sampled values, Edition 2.1 compatibility checks, and configuration of GOOSE/SV supervision (LGOS, LSVS) — [Hitachi Energy release notes, FP6](https://new.abb.com/news/detail/61226/release-of-integrated-engineering-tool-iet600-version-53-feature-pack-6)
- IET600 has a formal UCAIug SCT (System Configuration Tool) certification record — see Q3.

**GE EnerVista family**
- No product literally named "EnerVista CET" was found. GE's UR-series IEDs are configured via EnerVista UR Setup, which can import an SCD file and extract settings for any UR devices it contains (right-click → "Import Contents From SCD File") — [manualslib.com — GE UR-series manuals](https://www.manualslib.com/manual/1330621/Ge-L60.html?page=664)
- EnerVista 3 Series Setup has an IEC 61850 configurator with ICD/CID, Settings, Reports, GOOSE Reception and GOOSE Transmission sections — [manualslib.com — GE 350 manual](https://www.manualslib.com/manual/1281367/Ge-350.html?page=123)
- GE's standalone system-level tool, EnerVista Viewpoint Engineer, could import ICD files and generate SCD files, but it has been discontinued — [GE Grid Solutions — Viewpoint Engineer legacy page](https://www.gegridsolutions.com/Multilin/enervista/Viewpoint/engineer.htm)
- "CET850" appears in Sepam (Schneider Electric) documentation as a tool that "adapts the communication profile of the devices to the precise needs of the system" — this is a Schneider Electric tool, not confirmed as GE — [scribd.com — CET850](https://www.scribd.com/document/370368046/CET850)

**SEL AcSELerator Architect (SEL-5032)**
- Imports/exports Edition 1, 2 and 2.1 SCL files (SCD, ICD, CID, IID), detecting errors via automatic comparison against the standard — [SEL product brochure](https://selinc.com/api/download/141198)
- Bundled "Semantic XML Compare" tool diffs two SCL files; bundled "Schema Validator" checks SCL schema against published IEC 61850 editions — [SEL product brochure](https://selinc.com/api/download/141198)
- Workflow: SEL ICD imported → configured for GOOSE/SV/MMS → sent to device as CID or exported; can also import other vendors' SCL so SEL devices subscribe to their GOOSE/SV/MMS reports — [SEL product brochure](https://selinc.com/api/download/141198)
- Can view/edit the server data model (logical device/logical node/data object) for supported SEL devices — [SEL product brochure](https://selinc.com/api/download/141198)
- Per one SEL brochure, only SEL relays configure their communications directly from received SCL files (i.e., non-SEL device reconfiguration from SCL is not claimed) — [SEL product brochure](https://selinc.com/api/download/141198)

**Open-source: OpenSCD**
- Browser-based editor for SCL files under IEC 61850-6 Edition 2+, runs as an offline-capable progressive web app — [github.com/openscd/open-scd](https://github.com/openscd/open-scd)
- Plug-in architecture; community plug-ins tracked in a separate repo — [github.com/com-pas/oscd-official-plugins](https://github.com/com-pas/oscd-official-plugins)
- CoMPAS fork (`compas-open-scd`) adds a backend service for opening/saving SCL files, plus GOOSE/SV and reporting support, IED comparison, and SCL "cleanup" — [github.com/com-pas/compas-open-scd](https://github.com/com-pas/compas-open-scd); [LF Energy PAC World 2024 paper](https://lf-energy.atlassian.net/wiki/spaces/SHP/pages/32539033/Paper+-+PAC+World+Conference+2024)
- Apache 2.0 licensed, TypeScript; originated at OMICRON Electronics with contributions from Alliander, Transpower and others; hosted under LF Energy — [github.com/openscd/open-scd](https://github.com/openscd/open-scd); [lfenergy.org announcement](https://lfenergy.org/openscd-v0-33-0-now-available/)
- A separate lightweight community fork ("scl-editor") targets simpler, more maintainable long-term distribution for users who want to stay close to the standard — [github.com/danyill/scl-editor](https://www.github.com/danyill/scl-editor)

**Open-source: libIEC61850 and related SCL libraries**
- `libIEC61850` (mz-automation): GPLv3 client/server library implementing MMS, GOOSE and SV protocols — [awesome.ecosyste.ms mirror of mz-automation/libiec61850](https://awesome.ecosyste.ms/projects/github.com%2Fmz-automation%2Flibiec61850). Search results did not confirm whether it ships a dedicated SCL parser module.
- `go-iec61850` (otfabric): Go library with an `scl` package and a command-line tool `sclparse` that inspects, validates and queries SCD/ICD/CID/IID files; supports schema editions v1.7 through 2007C5 with auto-detection — [pkg.go.dev/github.com/otfabric/go-iec61850](https://pkg.go.dev/github.com/otfabric/go-iec61850)
- `scl-lib` (OpenEnergyTools): TypeScript library for IEC 61850 SCL, MIT licensed, distributed via npm — [github.com/OpenEnergyTools](https://github.com/OpenEnergyTools)
- `SCL_Loader` (RTE France): parses/loads IEC 61850 SCL files (system and IED level) into memory — [relatedrepos.com mirror of rte-france/SCL_Loader](https://relatedrepos.com/gh/rte-france/SCL_Loader)
- Older/likely unmaintained SCL parser repos from ~2011–2014 were also surfaced but not verified as active — gap noted below.

**Viewer/validator-only tools**
- Triangle MicroWorks **SCL Navigator**: creates, views, edits and verifies SCL files; can display SCL as raw XML or as an interpreted data-model tree; validation is powered by the **RiseClipse OCL Engine** (Object Constraint Language rules applied to the SCL file, pinpointing error locations, sortable/filterable); includes model-to-model comparison (classifying elements as Missing/Matched/Modified, added v1.3.1), automated formatting, search, drag-and-drop logical-node management; a free "SCL Reader" mode with RiseClipse Verify remains after a 14-day full trial — [Triangle MicroWorks — SCL Navigator overview](https://files.trianglemicroworks.com/products/testing-and-configuration-tools/scl-navigator-pages/overview); [digitalsubstation.com — OCL machine-readable rules for SCL validation](https://digitalsubstation.com/article/ocl-iec-61850-machine-readable-rules-scl-validation); [pacw.org — Compare models with SCL Navigator](https://www.pacw.org/compare-models-with-the-latest-release-of-scl-navigator)
- OMICRON **StationScout**: substation-automation testing tool; on loading an SCD file it visualizes all communication relationships in the substation and can show live data when connected; supports re-importing a single IED or the whole configuration from an updated SCL file while preserving existing test cases and custom signal names; can simulate missing IEDs/IOs — [pdf.directindustry.com — StationScout catalog](https://pdf.directindustry.com/pdf/omicron-electronics/stationscout-substation-automation-system-testing/13971-784195.html). No source confirmed OCL-style schema/semantic validation in StationScout (distinguishing it from SCL Navigator).

### Inferences
- Across named tools, there is a clear split between "system-level SCT" (produces/maintains the full-station SCD: Helinks STS, Siemens System Configurator, ABB/Hitachi IET600) and "IED-level configuration tool" (produces/consumes a single device's ICD/CID: SEL AcSELerator Architect, GE EnerVista UR Setup/3 Series). Several SCTs are themselves built to import ICD files from IED-level tools and merge them into an SCD — a two-tier engineering workflow recurs across vendors.
- No literal product named "IEC 61850 Explorer" could be confirmed to exist as a distinct commercial or open-source brand; requests for it likely refer to one of IEDExplorer (open-source), vendor "Explorer"-branded live-diagnostic tools (e.g., ITT600 SA Explorer), or generically to any SCL viewer/browser tool.

### Gaps
- Could not verify current (2025/2026) version numbers or full changelogs for several commercial tools (GE EnerVista CET specifically could not be confirmed to exist at all under that name — flagged, not guessed).
- Could not confirm whether `libIEC61850` ships its own SCL/ICD parsing utility versus relying on external XML tooling.
- Did not find independent (non-vendor) reviews or comparisons rating these tools against each other; all feature claims above are vendor-sourced or trade-press paraphrases of vendor material, which the researcher.md source-quality guidance flags as weaker evidence.

---

## Q3: IEC 61850 conformance/certification test tools and their role with SCL files

### Takeaway
UCAIug (UCA International Users Group) is primarily a certification/accreditation body, not a tool vendor: it accredits test laboratories, certifies conformance-test results (including a distinct "SCT" — System Configuration Tool — certification track), and organizes Interoperability Testing (IOP) events; actual conformance testing is performed with vendor tools such as OMICRON Test Universe (with IEDScout as a companion) or lab-internal tools like an "IEC 61850 Ed2 Client Conformance Verifier." SCL files are a direct input to these conformance tests: client/server test tools load the IED's capability/configuration description from SCL (ICD/CID) to drive automated protocol tests, and a specific certification track exists for SCTs' ability to correctly import/export/round-trip SCL.

### Cited Findings
- UCAIug performs three key functions in IEC 61850: accreditation of test laboratories for conformance testing, certification of conformance-test results, and organization of Interoperability Testing (IOP) events — [digitalsubstation.com — IEC 61850 conformance certificates](https://digitalsubstation.com/article/iec-61850-conformance-certificates-ucaiug-uca-testing-en)
- The UCAIug Test Procedure Working Group maintains test procedures via a Redmine tracker with dedicated sub-projects: SCL Tooling, Server, Client, GOOSE Performance — [digitalsubstation.com](https://digitalsubstation.com/article/iec-61850-conformance-certificates-ucaiug-uca-testing-en)
- Procedures build on IEC 61850-10 Edition 2 (methods, abstract test cases), but SCT/ICT-specific procedures went beyond its scope and were developed jointly by UCAIug and manufacturers — [digitalsubstation.com](https://digitalsubstation.com/article/iec-61850-conformance-certificates-ucaiug-uca-testing-en)
- A formal **"SCL tool" certification** exists: e.g., a DNV GL certificate for ABB PCM600 under an "SCLtoolEd2" procedure (revision 1.0) — [redmine.ucaiug.org certificate PDF](https://redmine.ucaiug.org/attachments/download/2267/16-2127_DNVGL_ABB_PCM600_SCLtoolEd2_Certificate%20-%20Formal.pdf)
- Client-device certificates record the specific test tool used, e.g. a KTL certificate for a client device citing use of "IEC 61850 Ed2 Client Conformance Verifier 1.0" together with a vendor network analyzer — [redmine.ucaiug.org — KEPCO KSE client certification](https://redmine.ucaiug.org/attachments/download/3203/24-041130-01-1_KEPCO_KSE_Client_Ed2.0_Certification_KTL.pdf); [redmine.ucaiug.org — Daonsys ECU-4784 client certification](https://redmine.ucaiug.org/attachments/download/2903/23-039475-02-2_Daonsys_ECU-4784_Client_Ed2_Certification_KTL.pdf)
- Certificates are centralized in the "Redmine Certificate Repository," with the UCA Testing website as the current official entry point; one secondary source cites counts of 1,302 server, 266 client, and 34 merging-unit certificate records (dated, unverified currency) — [digitalsubstation.com](https://digitalsubstation.com/article/iec-61850-conformance-certificates-ucaiug-uca-testing-en)
- Accreditation is per-laboratory, e.g. TECNALIA accredited by UCA as a Level A laboratory to certify IEC 61850 Edition 2 server devices (2018) — [tecnalia.com](https://www.tecnalia.com/en/news/accredited-by-uca-as-level-a-laboratory-to-certify-server-devices-according-to-iec-61850)
- OMICRON **Test Universe**: a 2013 OMICRON conference deck situates conformance testing under IEC 61850-10 (PICS/PIXIT/MICS documents, test procedures, cooperation with UCAIug) and notes that *functional* testing (as opposed to conformance testing) is not specified by the standard — [CIRED 2013 seminar deck](https://mail.ho-cired.hr/images/SEMINARI/2013_primjena_norme/CIRED-03.pdf)
- Test Universe's client/server test module (from v3.10) loads the IED description from an SCL file, connects over Ethernet, reads data, and runs automated tests; its GOOSE and Sampled Values configuration modules also take SCL as input — [CIRED 2013 seminar deck](https://mail.ho-cired.hr/images/SEMINARI/2013_primjena_norme/CIRED-03.pdf)
- Test Universe 4.30 added configurable datasets with up to 32 Sampled Values streams (IEC 61869-9 / IEC 61850-9-2 Ed2.1 scope), plus control services and virtual binary outputs in the client/server module — [pacw.org — Test Universe 4.30](https://www.pacw.org/test-universe-4-30)
- IEDScout (OMICRON) is positioned as a companion to Test Universe, with its own SCL parser used to "check the quality of the engineering files according to IEC 61850-6" ahead of/alongside testing — [pacw.org — Test Universe 4.30](https://www.pacw.org/test-universe-4-30)

### Inferences
- There appear to be (at least) three distinct, named certification tracks referenced in UCAIug materials: Server conformance, Client conformance, and SCT ("SCL tool") conformance — meaning SCD/ICD-authoring tools themselves (not just IEDs) can be certified for correct SCL import/export behavior (evidenced by the ABB PCM600 "SCLtoolEd2" certificate).
- Conformance testing and functional/interoperability testing are treated as distinct activities in UCAIug/OMICRON material; vendor tools like Test Universe and IEDScout support both, but UCAIug does not appear to supply its own general-purpose test-tool product — test houses use a mix of vendor tools (OMICRON Test Universe, in-house/lab-built verifiers such as the cited "Conformance Verifier").

### Gaps
- Could not find a current (2025–2026) authoritative list of UCAIug-endorsed or lab-standard conformance test tools; the "IEC 61850 Ed2 Client Conformance Verifier 1.0" appears only in certificate PDFs with no vendor/source page found.
- Could not confirm whether OMICRON Test Universe itself holds, or is required to hold, UCAIug tool certification, versus simply being used by certified labs.
- Did not find a current/updated certificate count or registry snapshot beyond the single secondary source citing 1,302 server / 266 client / 34 merging-unit certificates (undated precision risk).

---

## Q4: Per-tool technical summary (vendor, purpose, formats, capability type, technical notes)

### Takeaway
A consolidated comparison table of all tools researched, built strictly from the cited findings above; see Gaps for fields that could not be verified for a given tool.

### Cited Findings (consolidated table)

| Tool | Vendor | Primary purpose | File formats (in/out) | Edit / View / Validate / Live comms | Notable technical approach (per own docs) |
|---|---|---|---|---|---|
| IEDScout | OMICRON | Live IED exploration, MMS client, GOOSE subscribe/simulate | ICD, CID, SCD (read/parse); COMTRADE (GOOSE capture export) | View + Validate (SCL quality check) + Live (MMS, GOOSE) | Built-in SCL parser for IEC 61850-6 quality checks; combined client/server+GOOSE event list — [source](https://pdf.directindustry.com/pdf/omicron-electronics/iedscout/13971-614616.html), [source](https://www.pacw.org/test-universe-4-30) |
| StationScout | OMICRON | Substation-wide live testing/visualization | SCD (import, re-import per-IED) | View + Live (connects, simulates missing IEDs/IOs) | Visualizes all communication relationships directly from SCD; preserves test cases/signal names across re-import — [source](https://pdf.directindustry.com/pdf/omicron-electronics/stationscout-substation-automation-system-testing/13971-784195.html) |
| OMICRON Test Universe | OMICRON | Conformance/functional test platform (incl. protection testing) | SCL (IED description load for client/server, GOOSE, SV modules) | Validate + Live (automated protocol test execution) | Client/server test module loads IED description from SCL, runs over Ethernet; supports IEC 61869-9/61850-9-2 Ed2.1 SV — [source](https://mail.ho-cired.hr/images/SEMINARI/2013_primjena_norme/CIRED-03.pdf), [source](https://www.pacw.org/test-universe-4-30) |
| Helinks STS | Helinks (distributed via Triangle MicroWorks) | Top-down, multivendor system engineering (SCD authoring) | ICD, SCD (import/export), Excel import/export | Edit + Validate | Device-independent engineering per IEC 61850-4/-6; graphical single-line/function/system diagram editors; vendor "packages" needed for vendor-specific SCD generation — [source](https://dtpartners.com.au/?p=3110) |
| Siemens IEC 61850 System Configurator (in DIGSI 5 Standard) | Siemens | Manufacturer-neutral system-level SCD engineering | ICD, IID, CID, SCD, SSD, SED | Edit (station/network/connection views) | "Network" and "Connection" views; SCD distributed to other tools (e.g., SICAM PAS) — [source](https://cache.industry.siemens.com/dl/files/201/109770201/att_994358/v1/SysConHelp_en.pdf) |
| ABB/Hitachi Energy IET600 | ABB / Hitachi Energy | System-wide IEC 61850 communication dataflow engineering | SCD, CID (import or manual creation of datasets/RCBs/GOOSE/SV control blocks) | Edit + Validate (has formal SICS, UCAIug SCT certification) | Graphical topology/comms editors; signed-SCL (IEC 62351) support; LGOS/LSVS supervision config — [source](https://library.e.abb.com/public/0c3ca16492c542d8b9663ab8e2c35488/2015%20Simulation%20and%20Testing%20Methodologies_Self.pdf), [source](https://new.abb.com/news/detail/61226/release-of-integrated-engineering-tool-iet600-version-53-feature-pack-6) |
| GE EnerVista UR Setup / 3 Series Setup / Viewpoint Engineer (discontinued) | GE (Grid Solutions) | IED-level (UR/3-Series) configuration; Viewpoint Engineer was system-level | SCD (import, UR Setup); ICD import + SCD generation (Viewpoint Engineer, discontinued) | Edit (device-level) | Right-click "Import Contents From SCD File" workflow; 3 Series has dedicated ICD/CID + GOOSE Rx/Tx config sections — [source](https://www.manualslib.com/manual/1330621/Ge-L60.html?page=664), [source](https://www.manualslib.com/manual/1281367/Ge-350.html?page=123) |
| SEL AcSELerator Architect (SEL-5032) | SEL | IED-level configuration + SCL validation utilities | SCD, ICD, CID, IID (Ed1/Ed2/Ed2.1 import/export) | Edit + Validate (bundled Schema Validator, Semantic XML Compare) | Bundled schema validator checks against published IEC 61850 editions; semantic diff tool; server data-model (LD/LN/DO) viewer/editor for SEL devices — [source](https://selinc.com/api/download/141198) |
| OpenSCD (+ CoMPAS fork) | LF Energy / community (originated at OMICRON) | Open-source browser-based SCD/system editor | SCL per IEC 61850-6 Ed2+ | Edit + Validate (CoMPAS adds IED comparison, SCL cleanup) | Progressive web app (offline-capable); plug-in architecture; CoMPAS fork adds backend service, GOOSE/SV/reporting support, IEC 60870-5-104 support — [source](https://github.com/openscd/open-scd), [source](https://github.com/com-pas/compas-open-scd) |
| SCL Navigator | Triangle MicroWorks | Standalone SCL viewer/editor/validator | SCL (all types) | View + Edit + Validate | Uses RiseClipse OCL Engine (Object Constraint Language) for rule-based validation with source-located errors; model-to-model comparison (Missing/Matched/Modified) — [source](https://files.trianglemicroworks.com/products/testing-and-configuration-tools/scl-navigator-pages/overview), [source](https://digitalsubstation.com/article/ocl-iec-61850-machine-readable-rules-scl-validation) |
| libIEC61850 | mz-automation | Open-source MMS/GOOSE/SV client-server protocol library | N/A confirmed for SCL specifically | Live (protocol stack); SCL parsing unconfirmed | GPLv3 licensed protocol implementation — [source](https://awesome.ecosyste.ms/projects/github.com%2Fmz-automation%2Flibiec61850) |
| go-iec61850 / sclparse | otfabric (open source) | SCL inspection/validation/query CLI | SCD, ICD, CID, IID | Validate (CLI) | Auto-detects schema edition (v1.7 through 2007C5) — [source](https://pkg.go.dev/github.com/otfabric/go-iec61850) |
| scl-lib | OpenEnergyTools (open source) | SCL manipulation library for JS/TS tooling | SCL | Library (used to build edit/view tools) | TypeScript, MIT licensed, npm-distributed — [source](https://github.com/OpenEnergyTools) |
| SCL_Loader | RTE France (open source) | In-memory SCL parsing/loading | SCL (system and IED level) | Library | — [source](https://relatedrepos.com/gh/rte-france/SCL_Loader) |
| IEDExplorer | Open source (Pavel Charvat, SourceForge) | Educational/testing MMS client | SCL (XML-parse variant only) | View + Live (MMS) | Variant adds a dedicated SCL XML parser — [source](https://sourceforge.net/p/iedexplorer/wiki/Home/) |

### Inferences
- The table shows a consistent three-way split in the market: (1) OMICRON-style live test/exploration tools that treat SCL as a convenience input, (2) vendor SCTs/IED tools that treat SCD/ICD authoring and round-tripping as their core deliverable, and (3) dedicated validators/libraries (SCL Navigator, go-iec61850, scl-lib, SCL_Loader) that exist purely to parse/validate/check SCL correctness, often used as building blocks inside category (2) tools.

### Gaps
- Could not independently verify claimed schema-edition support matrices (Ed1 / Ed2 / Ed2.1 / IEC 61850-9-2LE) for every tool in the table; these are drawn from vendor marketing/brochures rather than technical datasheets with explicit version matrices for the current 2026 releases.
- Could not confirm "Kalkitech" SCL tooling (named in the assignment's suggested sources) — no search was run for it specifically within the 15-call budget; should be treated as an open item for follow-up research.

---

## Q5: Features common across most/all SCL tools

### Takeaway
Across the researched tools, the recurring common capabilities are: SCL schema validation (against IEC 61850-6 editions), tree/model views of the IED logical-node structure, dataset/GOOSE/report configuration handling, import/export round-tripping between SCD and ICD/CID, and (for the more mature commercial tools) some form of cross-file/version comparison.

### Cited Findings
- Schema/standard validation appears in SEL Architect (Schema Validator), Siemens System Configurator/DIGSI (import/export of all SCL types implies schema-aware parsing), SCL Navigator (RiseClipse OCL rule engine), go-iec61850's sclparse (schema edition auto-detection and validation), and IEDScout (SCL parser "to check the quality of the engineering files") — [SEL brochure](https://selinc.com/api/download/141198); [pkg.go.dev go-iec61850](https://pkg.go.dev/github.com/otfabric/go-iec61850); [pacw.org](https://www.pacw.org/test-universe-4-30)
- Tree/model views of logical device/logical node/data object structure appear in SEL Architect (server model view/edit) and are implied by SCL Navigator's "interpreted data model" display mode — [SEL brochure](https://selinc.com/api/download/141198); [Triangle MicroWorks SCL Navigator overview](https://files.trianglemicroworks.com/products/testing-and-configuration-tools/scl-navigator-pages/overview)
- Dataset/GOOSE/Report Control Block/Sampled Value configuration is explicitly supported in IET600 (ABB), GE EnerVista 3 Series Setup (GOOSE Rx/Tx sections), and SEL Architect (configure ICD for GOOSE/SV/MMS) — [ABB webinar](https://library.e.abb.com/public/0c3ca16492c542d8b9663ab8e2c35488/2015%20Simulation%20and%20Testing%20Methodologies_Self.pdf); [GE 350 manual](https://www.manualslib.com/manual/1281367/Ge-350.html?page=123); [SEL brochure](https://selinc.com/api/download/141198)
- SCD↔ICD/CID import/export round-tripping is explicit in nearly every engineering tool surveyed: Helinks STS, Siemens System Configurator, IET600, GE EnerVista (UR Setup, Viewpoint Engineer), SEL Architect, and OpenSCD/CoMPAS — see individual citations in Q2/Q4 above.
- Comparison/diff functionality appears in SCL Navigator (model-to-model comparison), SEL Architect (Semantic XML Compare), and CoMPAS/OpenSCD (IED comparison) — [Triangle MicroWorks SCL Navigator](https://files.trianglemicroworks.com/products/testing-and-configuration-tools/scl-navigator-pages/overview); [SEL brochure](https://selinc.com/api/download/141198); [LF Energy PAC World 2024 paper](https://lf-energy.atlassian.net/wiki/spaces/SHP/pages/32539033/Paper+-+PAC+World+Conference+2024)

### Inferences
- "SCD/ICD round-trip import-export" is close to a universal baseline requirement among engineering tools in this space, likely because it is the mechanism by which the standard's two-tier (system engineering + IED engineering) workflow is implemented in practice (IEC 61850-6 process model), not purely a vendor choice.
- Comparison/diff tooling appears to be converging toward a standard feature (present in 3+ independently-vendored tools surveyed), suggesting it is becoming an expected baseline rather than a differentiator, even though it was historically a differentiator.

### Gaps
- Could not find a documented "engineering version/history tracking" feature (e.g., changelog/revision history inside the SCD file itself, beyond the SCD header's own revision field referenced for IET600) in any tool surveyed; this may be a gap in current tooling or simply undocumented in the public sources found.
- Could not confirm cross-reference/consistency checking (e.g., validating GOOSE subscriber/publisher consistency across IEDs in one SCD) as a named, specific feature in most tools; IET600's dataflow design and StationScout's "visualize all communication relationships" are the closest confirmed analogues, but explicit "consistency checker" terminology was not found.

---

## Q6: Features that differentiate tools from each other

### Takeaway
The clearest differentiators across the surveyed landscape are: (1) live device communication capability (MMS/GOOSE/SV) versus file-only tooling, (2) graphical single-line/topology diagram editing, (3) formal third-party conformance/SCT certification, (4) open-source/extensible plug-in or library architecture versus closed commercial product, and (5) breadth of multi-vendor IED support versus single-vendor-only tools.

### Cited Findings
- **Live communication**: IEDScout, StationScout, and OMICRON Test Universe all connect to and exercise live IEDs over MMS/GOOSE/SV — [IEDScout brochure](https://pdf.directindustry.com/pdf/omicron-electronics/iedscout/13971-614616.html); [StationScout catalog](https://pdf.directindustry.com/pdf/omicron-electronics/stationscout-substation-automation-system-testing/13971-784195.html); [Test Universe CIRED deck](https://mail.ho-cired.hr/images/SEMINARI/2013_primjena_norme/CIRED-03.pdf) — versus SCL Navigator, go-iec61850/sclparse, scl-lib and SCL_Loader, which are file-only tools with no live-communication claim found.
- **Graphical topology/single-line diagram editing**: explicitly claimed for Helinks STS (single-line, function, and system diagram editors) and IET600 (graphical topology/communication-infrastructure editors) — [Triangle MicroWorks Helinks STS overview](https://products.trianglemicroworks.com/products/testing-and-configuration-tools/helinks-pages/overview); [ABB webinar](https://library.e.abb.com/public/0c3ca16492c542d8b9663ab8e2c35488/2015%20Simulation%20and%20Testing%20Methodologies_Self.pdf) — not confirmed for SEL Architect, GE EnerVista tools, or the open-source parser libraries.
- **Formal SCT (SCL-tool) conformance certification**: confirmed specifically for ABB PCM600 (DNV GL "SCLtoolEd2" certificate) and implied for IET600 (SICS document referencing mandatory/optional SCT features) — [DNV GL certificate](https://redmine.ucaiug.org/attachments/download/2267/16-2127_DNVGL_ABB_PCM600_SCLtoolEd2_Certificate%20-%20Formal.pdf); [ABB SICS](https://library.e.abb.com/public/bd354523bcbb4458be241235c6f053df/1KHL504752%20IET600%20SICS%20Implementation%20Conformance%20Statement.pdf) — no equivalent certification claim found for Helinks STS, Siemens System Configurator, SEL Architect, GE tools, or OpenSCD in the search results.
- **Open-source extensibility / plug-in architecture**: unique to OpenSCD/CoMPAS among the tools surveyed, with an explicit plug-in system and community-contributed plug-ins repository — [github.com/com-pas/oscd-official-plugins](https://github.com/com-pas/oscd-official-plugins); all commercial tools surveyed are closed/proprietary with no plug-in SDK mentioned in the sources found.
- **Multi-vendor IED support breadth**: Helinks STS explicitly markets "device-independent" engineering but notes vendor-specific "packages" are required for vendor SCD generation (i.e., multi-vendor support is real but packaged/licensed per-vendor) — [dtpartners.com.au](https://dtpartners.com.au/?p=3110) — versus GE EnerVista and SEL Architect, which are scoped primarily to their own vendor's IEDs (with SEL explicitly noting only SEL relays reconfigure directly from received SCL) — [SEL brochure](https://selinc.com/api/download/141198).
- **Scripting/API access**: Not clearly confirmed for any commercial GUI tool in the sources found; the clearest API/scripting-style access found is in the open-source libraries (go-iec61850's `sclparse` CLI, OpenEnergyTools' `scl-lib` npm package, RTE's `SCL_Loader`), which are designed to be embedded in custom scripts/pipelines rather than used as end-user GUIs — [pkg.go.dev go-iec61850](https://pkg.go.dev/github.com/otfabric/go-iec61850); [github.com/OpenEnergyTools](https://github.com/OpenEnergyTools); [relatedrepos.com rte-france/SCL_Loader](https://relatedrepos.com/gh/rte-france/SCL_Loader).

### Inferences
- Commercial SCT vendors appear to compete primarily on graphical engineering workflow depth (topology diagrams, multi-vendor device libraries) and formal certification, while the live-communication/testing tools (OMICRON's IEDScout/StationScout/Test Universe line) compete on protocol-level depth and simulation fidelity rather than SCL authoring depth.
- The open-source ecosystem (OpenSCD/CoMPAS, go-iec61850, scl-lib, SCL_Loader) differentiates itself less on end-user GUI polish and more on extensibility/embeddability — consistent with these being community/utility projects rather than turnkey commercial engineering suites.

### Gaps
- No direct, independent (non-vendor) benchmark or review comparing engineering-workflow depth, usability, or multi-vendor library breadth across Helinks STS, Siemens System Configurator, and IET600 was found; all breadth/usability claims above are vendor-sourced.
- Scripting/API access for the major commercial tools (Helinks STS, IET600, Siemens, SEL Architect) was not confirmed one way or the other within the search budget used — flagged as an open question rather than assumed absent.
- "Kalkitech" tooling (suggested in the assignment) was not researched due to the 15-call search budget being allocated to the explicitly named tools (OMICRON, Helinks, Siemens, ABB, GE, SEL, OpenSCD, libIEC61850, UCAIug) first; this is a clear follow-up item.
