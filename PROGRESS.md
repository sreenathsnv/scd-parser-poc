# Progress Log

Tracks what's done and what's left against
[plans/scl-explorer-agent-simulator-technical-plan.md](plans/scl-explorer-agent-simulator-technical-plan.md).
Update this file at the end of each phase/step.

## Done

### Phase 0 — Foundations (branch: `feature/phase-0-foundations`)
- SCL parser/serializer (Python, lxml): parses Header/Substation/IED/Communication/DataTypeTemplates,
  resolves `lnType -> LNodeType -> DOType -> DA`, retains `<Private>` blobs untouched,
  byte-identical no-op round trip on all four `Resources/` fixtures.
- Custom validation rules: 9.2.6 naming uniqueness, duplicate IP/MAC per SubNetwork,
  empty/misconfigured control blocks, dangling `lnType`/`ExtRef`, missing-Substation-in-`.scd`.
  Verified live: catches MAYZAN's duplicate `10.1.150.3` and DTech26's missing `<Substation>`.
- Validation sidecar (Java, RiseClipse wrapper): structural/XSD pass works.
  OCL semantic rules not populated yet (see Known follow-ups).
- Neo4j knowledge graph ingestion: full node/edge schema from the research report.
  Verified live against all three canonical queries (GOOSE subscribers, IEDs-on-SubNetwork,
  empty control blocks).
- FastAPI gateway: parse/validate/graph-load/save-as-copy/save-overwrite endpoints.
- `docker-compose.yml` core profile: all 7 services verified up together.
- model-generator, frontend: scaffolded as placeholders only (real work is Phase 3 / Phase 1).
- Re-verified from a clean slate (`docker compose down -v` -> rebuild -> `up`) on 2026-11-09:
  all 11 pytest tests, all 7 services, all 4 resource files parse/validate/graph-load correctly,
  all 3 canonical graph queries, zero error-level logs.

### Phase 1 — Explorer, increment 1 (branch: `feature/phase-1-explorer`)
- Backend: `GET /files/{name}/tree` full nested tree projection (Substation plant topology +
  IED->AccessPoint->Server->LDevice->LN->DOI->DAI), with resolved type info (lnType/CDC/FC/bType)
  alongside raw attributes, per plan component 4.
- Frontend: file picker, tree view (react-arborist) with node-details panel, validation panel —
  wired to live parse/tree/validate endpoints, no mock data.
- Tested live in browser against all four `Resources/` fixtures, including the largest
  (DTech26, ~39k graph nodes / 4.1MB tree JSON) — renders without hanging, correctly shows
  MAYZAN's duplicate-IP and DTech26's empty-Substation-group/165-warning validation results.
- Not yet done in Phase 1: DataTypeTemplates browser with "used by" back-links,
  inline editing of DOI/DAI values, save-as-copy/save-overwrite UI with confirmation dialog.

### Phase 1 — Explorer, increment 2 (branch: `feature/phase-1-explorer`)
- Backend: `GET /files/{name}/graph-view` — collapsed IED/control-block/dataset/SubNetwork
  dataflow graph (not the full DO/DA instance tree) in Cytoscape.js elements shape, per the
  plan's "click a DataSet -> see its PUBLISHES control block -> SUBSCRIBES_TO fan-out" example.
- Frontend: a Graph tab (cytoscape.js) with the same node-details panel as the tree view,
  lazily triggering graph-load + graph-view only when first opened.
- Two real bugs found and fixed while testing this live in the browser (not just unit tests):
  1. **Neo4j ingest concurrency race**: two overlapping `ingest()` calls (e.g. a slow
     backgrounded request plus a fresh UI-triggered one) could interleave a DELETE with
     another's in-flight MERGE, raising `Neo4j.ClientError: EntityNotFound`. Fixed with a
     `threading.Lock` serializing delete+reinsert in `graph/loader.py`.
  2. **Vite's file watcher misses bind-mounted edits on Docker Desktop/Windows**: a source
     edit landed on disk (confirmed via `docker compose exec`) but the running dev server
     kept serving the pre-edit module — classic inotify-across-the-VM-boundary limitation.
     Fixed with `watch: { usePolling: true }` in `vite.config.js`; a plain container restart
     also picks up current content if this recurs.
- Tested live: verified the exact node a click lands on gets selected in cytoscape AND
  reflected in the React details panel (not just "a graph renders"), on the ~39k-node
  DTech26 file.

## Left to do

- **Phase 1 — Explorer** (remaining): DataTypeTemplates browser, inline editing,
  save-as-copy/save-overwrite UI with confirmation dialog.
- **Phase 2 — Agent mode** (chat panel, fixed Cypher-template tool library,
  citation-grounded answers, LiteLLM-backed provider switching, verified across
  Anthropic/OpenAI/Gemini/Ollama).
- **Phase 3 — Simulator** (MMS + GOOSE via libiec61850/pyiec61850, `genconfig.jar`
  wrapper in model-generator, control API, self-verification harness).
- **Phase 3b — Simulator (SV)**, **Phase 3c — real-LAN GOOSE deployment** (follow-ons).
- **Pre-launch**: legal sign-off on the Simulator Service's GPLv3 process-isolation
  approach (or acquire MZ Automation's commercial libiec61850 license).

## Known follow-ups from Phase 0 (not oversights, tracked deliberately)

1. OCL semantic rule files not populated — see `services/validation-sidecar/README.md`.
2. IEC SCL XSD not vendored into this repo (IEC-EULA-licensed, not open-source) —
   same README, plus the root `README.md`.
3. Graph ingestion of a large SCD takes ~10-25s; fine for now, worth profiling
   before Phase 2's agent starts calling it interactively.
4. Vite's dev-mode HMR websocket doesn't reconnect through the reverse proxy (cosmetic
   console error only); a source edit in dev still needs a manual browser refresh.
