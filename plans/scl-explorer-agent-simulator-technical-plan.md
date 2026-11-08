# Technical plan: SCL Explorer, Agent Mode, and Auto-Simulator for IEC 61850 SCD/ICD/CID files

## Context
Trivium's SCD-POC has produced a research report ([reports/IEC 61850 SCL formats and tools.md](../../../../../d/Trivium-Inhouse/SCD-POC/reports/IEC%2061850%20SCL%20formats%20and%20tools.md)) establishing how SCL files are structured, how tools validate/parse them, how signal references resolve, and how the content maps onto a knowledge graph. This plan turns that research into a concrete build for three requested capabilities, informed by two further technical research passes (libiec61850's simulator-generation capability, and OpenSCD/graph-DB build-vs-reuse options):

1. **SCL Explorer** — browse and **edit** an SCD/ICD/CID file's IED/LDevice/LogicalNode/DataObject/DataAttribute structure, plus a **graph view** of the same content, plus validation results, with safe save-as-copy / save-overwrite-with-warning semantics.
2. **Agent mode** — ask natural-language questions about a loaded file's signals, structure, and defects, grounded in real parsed/graph data (not the LLM's own guesses).
3. **Auto-simulator generation** — spin up a running MMS/GOOSE (and later SV) simulator for a chosen IED straight from its SCD/ICD/CID definition, so a real client device can be tested against it.

Clarified constraints from the user:
- The tool **may ship to clients** eventually — this makes the GPLv3 license of the simulator engine (libiec61850) a real compliance question, addressed below via process isolation, not just a footnote.
- A **polyglot/multi-service backend is welcome** — use the right language per component rather than forcing one stack.
- The Explorer must support **editing** DA/DOI values (and other attributes) and other fields, with two save paths: **save as copy** (new file, no warning needed) and **save over the original file** (must show a confirmation warning before overwriting).

## Non-goals for v1 (explicitly out of scope, to keep the plan executable)
- Full graphical single-line-diagram editing (à la Helinks STS/IET600) — the Explorer edits attribute values and structure in the tree/graph view, not a drawn topology canvas.
- Automatic Sampled Values (SV) simulation — libiec61850 has no automatic SV wiring (confirmed by research; only GOOSE is automatic from the data model) and it isn't exposed in the Python bindings. SV is a defined Phase 3b follow-on, not a Phase-3 blocker, especially since only one of the four sample files (`DTech26_vPAC`) even defines `SampledValueControl`.
- Free-form LLM-generated Cypher in Agent mode v1 — the agent calls a fixed library of parameterized, read-only query templates (expandable later) instead of writing arbitrary graph queries, to avoid injection/incorrect-query risk.

## Architecture overview

```
                        ┌─────────────────────────┐
                        │   Explorer Web App       │  React + Cytoscape.js (graph view)
                        │  (tree view / graph view │  + a tree component (e.g. react-arborist)
                        │   / editor / chat panel) │  + a chat panel for Agent mode
                        └────────────┬─────────────┘
                                     │ REST / WebSocket
                        ┌────────────▼─────────────┐
                        │   API Gateway (Python,     │  FastAPI
                        │   FastAPI)                 │  orchestrates everything below
                        └───┬──────┬───────┬────────┘
             ┌──────────────┘      │       └───────────────────┐
┌────────────▼───────────┐ ┌──────▼─────────────┐   ┌──────────▼───────────┐
│ SCL Parser/Serializer   │ │ Validation sidecar  │   │ Agent Orchestrator    │
│ (Python, lxml)          │ │ (Java: RiseClipse   │   │ (Python, provider-    │
│ parse → resolved model  │ │  OCL validator,      │   │  agnostic via LiteLLM)│
│ → graph loader          │ │  run via Docker)     │   │ fixed Cypher-template │
│ edited model → XML      │ │ + custom checks       │   │ tools + resolver      │
│  writer (round-trips    │ │ (dup IP/MAC, 9.2.6)  │   │ calls; swaps Anthropic│
│  <Private> untouched)   │ └──────────────────────┘   │ /OpenAI/Gemini/Ollama │
└────────────┬────────────┘                            └──────────┬────────────┘
             │ nodes/edges                                         │ Cypher
┌────────────▼─────────────────────────────────────────────────────▼───────────┐
│                      Neo4j Community (Docker)                                 │
│   Property graph per the node/edge schema in the research report              │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│  Simulator Service — kept as its OWN deployable unit, isolated by design       │
│  because it embeds GPLv3 libiec61850 (see licensing note below)               │
│  Java: genconfig.jar (dynamic model/config generator, one IED at a time)      │
│  Python: pyiec61850-driven host process → IedServer + integrated GOOSE pub    │
│  gRPC/REST control API: start/stop, set DA values, scripted scenarios,         │
│  built-in MMS client + GOOSE subscriber for self-verification                 │
└───────────────────────────────────────────────────────────────────────────────┘
```

Why polyglot: the two best-fit SCL/IEC-61850 toolchains are in different languages — RiseClipse's OCL semantic validator and libiec61850's model-generator tools (`genmodel.jar`/`genconfig.jar`) are Java; libiec61850's runtime (server/GOOSE/MMS) is C with official-but-experimental Python bindings (`pyiec61850`); the richest web graph-visualization and tree-UI libraries are JS/TS. Rather than reimplementing any of these, each stays in its native language behind a small service boundary, called from the Python API gateway via subprocess/Docker/gRPC. Every service is containerized (see "Deployment & Dockerization" below), so the language mix is an internal implementation detail, not an install burden.

## Licensing note (acted on, not just flagged, because the answer was "may ship to clients")
libiec61850 is **GPLv3** (confirmed from its `COPYING` file), not the MPL-2.0 originally assumed. Because this tool may ship to clients, the Simulator Service must be architected so GPLv3 copyleft doesn't spread into Trivium's proprietary API/Explorer/Agent code:
- Run it as a **separate OS process/container**, communicating only over network RPC (gRPC/REST) — the classic "mere aggregation across a process boundary," not static/dynamic linking into a proprietary binary.
- Distribute the Simulator Service's own source (it's already open) alongside the product when shipped, satisfying GPLv3's distribution terms for that component specifically.
- Before first client shipment, get real legal sign-off on this isolation approach, or budget for MZ Automation's commercial libiec61850 license if Trivium prefers to avoid GPLv3 obligations entirely. Note this explicitly as a pre-launch checklist item, not a Phase 3 blocker for internal POC use.

## Component plan

### 1. SCL Parser & Serializer (Python, `lxml`)
- Parses Header/Substation/IED/Communication/DataTypeTemplates into a typed object model, performing the join described in the report: `lnType → LNodeType → DO → DOType → DA/SDO → DAType/EnumType/basic`, plus Communication cross-references (`ConnectedAP.iedName`, `GSE`/`SMV` → control block) and `ExtRef` subscriber resolution (Edition 1 value-based vs. Edition 2 `serviceType="GOOSE"` forms, branched explicitly).
- Retains every `<Private>` subtree as an opaque, untouched blob keyed by its `type` attribute — never reinterpreted, always round-tripped (per report §"Underneath the XML").
- **Serializer (new requirement for editing):** writes the (possibly edited) object model back to schema-valid SCL XML, preserving attribute order/namespace declarations and all untouched `<Private>` blobs byte-for-byte, so a save-and-reopen round trip is lossless outside the fields the user actually changed.
- Validates against the official SCL XSD set (`SCL.xsd` + 7 cooperating schemas), vendored from the open-source `compas-scl-xsd` repo, edition-gated by the `<SCL>` root's version/revision attributes.

### 2. Validation sidecar (Java: RiseClipse + custom rules)
- Runs RiseClipse's SCL validator (Docker image `riseclipse/riseclipse-validator-scl`) for IEC TS 61850-6-3 OCL semantic rules (dangling references, missing mandatory objects, etc.) instead of reimplementing OCL rule-checking.
- Adds a small custom-rules module (Python, inside the API gateway) for checks the report flagged as needing explicit handling: clause 9.2.6 naming-uniqueness (`iedName, ldInst, prefix, lnClass, lnInst`), duplicate IP/MAC within a SubNetwork, and "empty/misconfigured" control blocks (a `GSEControl`/`ReportControl` whose `datSet` resolves to zero FCDA members).
- Output is one structured, severity-tagged data-quality report per file — this is a first-class deliverable, not something the graph or UI silently papers over (the report's central risk warning).

### 3. Knowledge Graph (Neo4j Community, Docker)
- Loads the resolved object model into the node/edge schema already designed in the research report (`IED`/`LDevice`/`LogicalNode`/`DataObject`/`DataAttribute`/`LNodeType`/`DOType`/`DataSet`/`FCDA`/`GSEControl`/`SampledValueControl`/`ReportControl`/`SubNetwork`/`ConnectedAP`, joined by `CONTAINS`/`INSTANCE_OF`/`TYPED_AS`/`PUBLISHES`/`SUBSCRIBES_TO`/`ASSOCIATED_WITH`/`ON` edges).
- Batch-loaded keyed by the file's own `Header`/`configRev`; re-ingestion on save replaces that file's subgraph.
- Chosen over Kuzu (embeddable, but its maintainer/company was just acquired and the repo archived — too risky to build on now) and over Memgraph (ambiguous community-license wording vs. Neo4j's unambiguous GPLv3 self-hosted terms). Accessed via the official `neo4j` Python driver from FastAPI.

### 4. Explorer Web App (React)
- **Tree view**: Substation → VoltageLevel → Bay → ConductingEquipment and IED → AccessPoint → Server → LDevice → LN0/LN → DO → DA, each node showing resolved type info (CDC, FC, bType) next to raw SCL attributes. A separate DataTypeTemplates browser (LNodeType/DOType/DAType/EnumType) with "used by" back-links powered by the graph.
- **Graph view (new requirement)**: an interactive node-link view of the same content via a graph-rendering library (Cytoscape.js — mature, handles the label/edge-type styling this schema needs), backed by live Neo4j queries (e.g. click a `DataSet` → see its `PUBLISHES` control block → `SUBSCRIBES_TO` edges fanning out to other IEDs). This is the direct, visual complement to the tree view, not a replacement for it.
- **Validation panel**: XSD + RiseClipse + custom-rule findings, severity-tagged, click-to-jump into the tree/graph node it concerns. Use the four existing resource files as built-in acceptance fixtures (MAYZAN's duplicate IPs, DTech26's missing `Substation`, the ICD's zeroed `Services`, `project.scd`'s placeholder values all become concrete, already-known test cases).
- **Editing**: inline edit of `DOI`/`DAI` values and other editable attributes (names, descriptions, IPs, etc.), tracked as a diff against the loaded model; re-runs validation live so a bad edit is visible before saving, not after.
- **Save UX** (exact behavior requested):
  - **Save as copy** — prompts for a new filename/path, writes via the serializer, original file untouched, no warning needed.
  - **Save (overwrite original)** — shows a confirmation dialog naming the exact file path and stating the overwrite is irreversible, before writing; only proceeds on explicit confirmation. This mirrors the general safety principle of confirming irreversible, destructive actions.
  - Every save re-runs the full validation pipeline and reloads the graph for that file.

### 5. Agent mode (Python, provider-agnostic LLM tool-use)
- Tool set: `resolve_object_reference(path)`, `get_logical_node(ied, ld, ln)`, `list_subscribers(ied)`, `list_publishers_for(ied)`, `find_misconfigured_blocks()`, `get_validation_issues(file)`, and a small named-query library covering the report's example questions ("which IEDs subscribe to GOOSE from IED X," "find empty ReportControl blocks," "list IEDs on SubNetwork Y with their IPs," etc.) as parameterized Cypher, not free-form generation.
- System prompt requires the agent to answer only from tool results, always cite the file/IED/LN path behind an answer, and explicitly say "this reference does not resolve" rather than guessing when a signal path is dangling — directly reflecting the report's warning that a polished interface can make upstream data defects look authoritative.
- UI: a chat panel beside the Explorer; clicking a cited reference in an answer navigates the tree/graph view to that node.
- **Provider flexibility (new requirement)** — see the dedicated "LLM provider flexibility" section below for the abstraction approach, supported providers, and the tool-calling-fidelity caveat for local models.

### 6. Simulator Service (isolated, GPLv3 boundary — see licensing note)
- **Model generation**: the Explorer's "Simulate this IED" action extracts the single chosen IED's SCL subset and shells out to libiec61850's `genconfig.jar` (the dynamic/config-file generator — no C recompilation needed per change), producing a `.cfg` model file. (`genmodel.jar`'s static C-source path is kept as a documented fallback for cases needing a standalone compiled binary rather than the Python host below.)
- **Runtime host**: a generic Python process using the official `pyiec61850` bindings loads the `.cfg` via `ConfigFileParser_createModelFromConfigFileEx`, creates an `IedServer`, binds it to an assigned IP:port, and calls `IedServer_enableGoosePublishing` — giving a working MMS server plus automatic GOOSE publishing for that IED's datasets purely by updating data-attribute values (`IedServer_updateFloatAttributeValue`, etc.), with no manual GOOSE-frame coding needed.
- **Conflict handling**: before starting, reuse Phase-0's duplicate-IP/placeholder-IP findings (e.g. MAYZAN's three IEDs sharing `10.1.150.3`, or `0.0.0.0` SNTP placeholders) to auto-remap a simulated IED to a free local port/loopback address instead of failing outright.
- **Control API**: REST/gRPC for start/stop/list, setting DA values on demand, and scripted scenarios (ramp a measurement, toggle a breaker position, play a protection-trip sequence) for repeatable client-device test suites.
- **Self-verification harness**: the same bindings also drive a built-in MMS test client and GOOSE subscriber, so the tool can confirm a spun-up simulator actually publishes what its `DataSet` declares *before* handing it to an external client device — this is the concrete answer to "test whether SCD/ICD/CID configurations work as expected."
- **Phase 3b (follow-on, not v1-blocking): Sampled Values.** No automatic SV wiring exists even in C, and `sv_publisher.h` isn't exposed in the stock Python bindings. This needs purpose-built glue: read `<SampledValueControl>`+`<DataSet>` from our own parsed model and drive the standalone `SVPublisher` C API (via a small C shim or an extended SWIG interface) to emit simulated analog waveforms at the configured sample rate. Scope after MMS/GOOSE prove out; `stevenblair/rapid61850` (closest prior art for SCD→GOOSE+SV code generation) is worth a short evaluation spike for ideas, but its 2020-era, proof-of-concept status means it should inform design, not be depended on directly.

## LLM provider flexibility
The user asked for Agent mode to work against Anthropic, OpenAI, Gemini, Ollama, "etc." interchangeably, not locked to one vendor.

- **Abstraction layer: LiteLLM** (MIT-licensed, actively maintained) as the Agent Orchestrator's only LLM-facing dependency, instead of hand-writing four separate SDK integrations. LiteLLM normalizes both plain completion calls and tool/function-calling across Anthropic, OpenAI, Google Gemini, and Ollama (plus Azure/Bedrock for later, at no extra cost) behind one interface, so the fixed Cypher-template tool set from Component 5 is defined once and works unchanged regardless of which provider is selected.
- **Deployment shape**: run LiteLLM as its own small proxy container (`llm-proxy`) presenting a single OpenAI-compatible endpoint; the Agent Orchestrator always talks to that one endpoint, and switching providers is a config change to the proxy, not a code change or redeploy of the orchestrator.
- **Configuration**: `.env`-driven — `LLM_PROVIDER` (`anthropic|openai|gemini|ollama`), `LLM_MODEL`, and the matching API key variable (`ANTHROPIC_API_KEY`/`OPENAI_API_KEY`/`GEMINI_API_KEY`); Ollama needs no API key but an `OLLAMA_BASE_URL` pointing at a reachable Ollama server (see the `ollama` compose service below). Switchable per-deployment (e.g. a hosted provider for most users, Ollama for an air-gapped/offline site), and the design should allow a future per-session override if Trivium wants users choosing their own model.
- **Tool-calling fidelity caveat (real risk, not hypothetical)**: function/tool-calling reliability is not equal across providers or, for Ollama, across models. Anthropic Claude (3.5+), OpenAI's `gpt-4o`/`gpt-4.1`/`o`-series, and Gemini 1.5/2.x Pro/Flash all have mature native tool-calling and should be treated as the trustworthy default for anything client-facing. For Ollama, tool-calling support is **model-dependent** (e.g. Llama 3.1+, Qwen2.5, Mistral Nemo support it; many smaller/older local models don't, or support it unreliably) — maintain a short "verified compatible local models" list in the deployment docs, and have the Agent Orchestrator detect/degrade gracefully (clearly tell the user tool-grounded answers aren't available) rather than silently falling back to an ungrounded free-text answer if a selected model's tool-calling can't be confirmed working. This directly protects the report's core epistemic-honesty requirement — an agent mode that can't ground its answer must say so, not guess.

## Deployment & Dockerization
Every component is containerized; nothing runs bare-metal in the delivered product.

| Service | Base | Purpose | Network notes |
|---|---|---|---|
| `frontend` | Node build → Nginx static | Explorer React app | Served behind `reverse-proxy` |
| `api-gateway` | Python/FastAPI | Orchestrates parsing, validation, graph, agent, simulator calls | Standard bridge network |
| `neo4j` | Official `neo4j` image (Community) | Knowledge graph | Bridge network; `neo4j_data` named volume for persistence |
| `validation-sidecar` | Java, built on `riseclipse/riseclipse-validator-scl` + a thin HTTP wrapper | XSD + OCL semantic validation | Bridge network; stateless |
| `model-generator` | Java (libiec61850's `genmodel.jar`/`genconfig.jar` + a thin HTTP wrapper) | Per-IED model/config generation for the simulator | Bridge network; stateless |
| `simulator-service` | Multi-stage build: C build stage (compiles libiec61850) → slim Python runtime with `pyiec61850` | MMS server + GOOSE publisher per simulated IED; isolates the GPLv3 dependency (see licensing note) | **Needs special networking — see caveat below** |
| `llm-proxy` | `litellm` image | Unified OpenAI-compatible endpoint in front of Anthropic/OpenAI/Gemini/Ollama | Bridge network; holds the provider API keys |
| `ollama` (optional, compose **profile**: `local-llm`) | Official `ollama/ollama` image | Local/offline LLM serving, only started when Ollama is the selected provider | Bridge network; named volume for pulled models |
| `reverse-proxy` | Nginx or Traefik | Single entry point, routes `/api` → `api-gateway`, `/` → `frontend`, TLS termination | Only service with a published host port in a client deployment |

Composition details:
- A base `docker-compose.yml` defines the always-on `core` set (`frontend`, `api-gateway`, `neo4j`, `validation-sidecar`, `model-generator`, `llm-proxy`, `reverse-proxy`); `simulator-service` and `ollama` sit behind Compose **profiles** (`simulator`, `local-llm`) so a pure Explorer+Agent deployment doesn't have to pull/run the GPLv3 component or a local model server it doesn't need.
- `docker-compose.override.yml` (dev only) adds bind-mounted source volumes and hot-reload for `api-gateway`/`frontend`; the base file stays production-shaped.
- **File access for save-as-copy / save-over-original**: the user's real SCD/ICD/CID files live on the host filesystem (e.g. this project's `resources/` folder). `api-gateway` bind-mounts that host directory into the container at a fixed path (Docker Desktop on Windows supports this), so "save over original" genuinely writes back to the host file the user opened, not just container-internal storage; this needs to be an explicit, user-visible configured path, not an assumption.
- **Secrets**: `.env.example` is committed; the real `.env` (Neo4j credentials, per-provider LLM API keys) is gitignored and, for any client-shipped deployment, should move to Docker secrets or an external vault rather than plain environment variables in compose files.
- **GOOSE networking caveat (important, flagged explicitly rather than discovered late)**: GOOSE is OSI **Layer-2 Ethernet multicast**, not plain TCP/IP. Standard Docker bridge networking (NAT) generally does not forward raw multicast frames between a container and the physical LAN, so an external client device on the real test network will not see GOOSE frames from a `simulator-service` container on a default bridge network. MMS (TCP/IP) has no such limitation and works fine over normal bridge networking with published ports. Two deployment variants follow from this:
  - **Same-host verification** (CI, local dev, the built-in self-verification harness): default bridge networking is sufficient, since the GOOSE subscriber and publisher can be co-located on the same Docker bridge.
  - **Real external-device GOOSE testing**: requires running `simulator-service` on a **Linux Docker host** with `network_mode: host`, or a `macvlan`/`ipvlan` network giving the container its own MAC/IP directly on the physical test LAN. This is **not fully supported the same way on Docker Desktop for Windows/Mac** (the environment this plan was written in) — document this as a deployment requirement distinct from a Windows dev machine, not an assumption baked into the default compose file.

## Phased delivery

| Phase | Deliverable | Key fixtures/acceptance check |
|---|---|---|
| 0 — Foundations | Parser+serializer, XSD+RiseClipse+custom validation, Neo4j ingestion, FastAPI gateway, **base `docker-compose.yml` for the `core` profile** | `docker compose up` (core profile) brings up frontend/api-gateway/neo4j/validation-sidecar/model-generator/llm-proxy/reverse-proxy cleanly; all four resource files parse without crashing; MAYZAN's known duplicate-IP defect and DTech26's missing-Substation gap both surface in the validation report automatically |
| 1 — Explorer (view + edit + save) | Tree view, graph view, validation panel, inline editing, save-as-copy/save-overwrite-with-warning | Edit a DAI value in `DTech26_vPAC...scd`, save as copy, reopen the copy and confirm the edit persisted and the original file is byte-identical to before |
| 2 — Agent mode | Chat panel, fixed tool/query library, citation-grounded answers, **LiteLLM-backed provider abstraction** | Ask "which IEDs subscribe to GOOSE published by FA01KF202" against the ingested DTech26 graph via the default hosted provider, then re-run the same question after switching `LLM_PROVIDER` to each of Anthropic/OpenAI/Gemini and to Ollama (`local-llm` profile) with a verified-compatible model, confirming identical tool calls and equivalent grounded answers each time |
| 3 — Simulator (MMS + GOOSE) | Single-IED extraction → `genconfig.jar` → Python host → running MMS server with GOOSE publishing + control API + self-verification harness, **`simulator-service` container (compose `simulator` profile)** | Simulate one IED from `IEC61850.icd` (simplest single-IED file) via the containerized service; confirm an MMS client (e.g. libiec61850's own example client) can read a data attribute, and the built-in GOOSE subscriber receives the configured dataset when a value changes, within the default bridge-network (same-host) setup |
| 3b — Simulator (SV, follow-on) | SVPublisher glue code for `<SampledValueControl>` datasets | Simulate SV output for `DTech26_vPAC`'s 6 `SampledValueControl` blocks; confirm sample rate/content matches the SCD's `smpRate`/dataset definition |
| 3c — Real-LAN GOOSE deployment (follow-on) | Linux-host `macvlan`/`network_mode: host` compose variant for `simulator-service` | Spin up the simulator on a Linux Docker host bound to a real test LAN segment; confirm an actual external client device (not another container) receives the GOOSE frames |
| Pre-launch (before any client shipment) | Legal sign-off on the GPLv3 process-isolation approach, or acquisition of MZ Automation's commercial license | N/A — a compliance gate, not a code deliverable |

## Verification plan
- Unit-test the parser/serializer round-trip (parse → no-op save → byte-diff against original) on all four resource files as the first CI gate, since a silent corruption here would undermine every other feature.
- Validation-report snapshot tests pinned to the specific defects already confirmed by hand in this conversation's earlier analysis (MAYZAN duplicate IPs/missing ConductingEquipment/no CSWI-XSWI; DTech26 missing Substation; the ICD's zeroed Services/missing LPHD; `project.scd`'s placeholder values) — regressions here are easy to catch because the expected findings are already known.
- Agent-mode answers spot-checked against manual graph traversal for at least the five example questions in the research report before trusting it for anything client-facing, and re-checked across every supported LLM provider (not just the default) since tool-calling fidelity varies by provider/model.
- Simulator Phase 3 acceptance run: start a simulator, connect with an independent MMS client and GOOSE listener (not the tool's own verification harness) to confirm the "works as expected" claim isn't self-referential.
- `docker compose config` + a clean `docker compose up` from a fresh checkout (no pre-existing local state) as a standing CI gate, so "dockerized entirely" stays true rather than drifting as services are added.
