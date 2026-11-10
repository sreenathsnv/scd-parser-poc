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

### Phase 1 — Explorer, increment 3 (branch: `feature/phase-1-explorer`)
- Backend: `app/scl/editor.py` mutates a DAI value in both the lxml tree (for the
  serializer) and the typed model (for live re-validation/re-projection) and marks the
  document dirty; `POST /files/{name}/edit/dai` exposes it.
- Frontend: inline edit box + Save button for `DataAttribute` tree nodes; after saving,
  the tree and validation report both re-fetch live (a bad edit becomes visible as a new
  validation finding before the user saves to disk, per the plan).
- Frontend: a custom `SaveAsCopyDialog` / `OverwriteConfirmDialog` (not native
  `window.prompt`/`confirm`, which turned out to be silently auto-dismissed in this
  session's automated browser harness and are poor UX generally) naming the exact file
  path and the overwrite's irreversibility; the overwrite button stays disabled with no
  pending edits.
- One correctness bug found before it could ship: `doc.dirty` was being used for two
  different things (the serializer's permanent "lxml tree has diverged from raw_bytes"
  flag, and the UI's "unsaved changes" indicator). Resetting it after save-overwrite (to
  clear the UI indicator) would have made the serializer's `if not dirty: return
  raw_bytes` fast path silently serve stale pre-edit bytes on a later save-as-copy. Split
  into two fields -- `dirty` (permanent) and `unsaved` (UI-facing, reset on overwrite only)
  -- with a regression test (`test_overwrite_then_save_as_copy_keeps_edit`) locking it in.
- Also fixed in passing: the tree projection never rendered nested `<SDI>` structures at
  all (only direct `DAI` children of a `DOI`); `_sdi_node` now recurses into them, which
  the DAI editor's `doiPath` needed to be correct for anyway.
- Tested live: edited `IEC61850.icd`'s `NamPlt/vendor` from "Siemens" to "TriviumTest"
  through the UI, saved as copy, confirmed the new file on disk has the edit and the
  original is byte-identical to before (`git status` clean on `Resources/`).
- Not yet done in Phase 1: DataTypeTemplates browser with "used by" back-links.

### Bug fix: cross-file data mixing in the Explorer (2026-11-09)
User-reported: switching files quickly (e.g. MAYZAN -> another file before MAYZAN's
slower parse/tree/validate finished) could show a *different* file's IED under the
selected file's name -- `openFile` in `App.jsx` never cleared the previous file's
`tree`/`report` state before fetching the new one, and had no request-sequencing guard,
so a slower response for an older selection could resolve after a faster one and
silently overwrite the correct data. Fixed with a request-token ref: each `openFile`/
`openGraphTab` call is stamped with a token, and any response whose token no longer
matches the latest call is discarded rather than applied. `tree`/`report` are now also
cleared immediately on file switch (shows "Loading {file}..." instead of stale content).
Verified against the backend directly first (MAYZAN parses to its own 11 real IEDs, 1
Substation -- no "TEST_01" anywhere; the file's own empty `ConductingEquipment` lists
are a genuine pre-existing defect in that fixture, not a parsing bug), then re-verified
the fix live by rapid-clicking between files in both directions (small-then-large and
large-then-small) and confirming the display never showed the wrong file's data.

### Feature: file import (2026-11-09)
User-requested: files shouldn't just be auto-discovered from a shared directory --
there should be an explicit import step, and all operations run against the imported
copy. Added `POST /files/import` (multipart upload): saves the file into its own
`imported/` subfolder under `SCD_FILES_DIR` (never overwriting an existing import --
collisions get a `-2`, `-3`, ... suffix), parses it immediately, and returns its summary.
Frontend: an "Import file..." button (hidden `<input type="file">`) in the sidebar,
which now shows two sections -- "Imported" and "Example fixtures" -- so the four
research fixtures are never confused with a user's own files.

This needed every `{filename}` route (`parse`, `tree`, `validate`, `edit/dai`,
`save-as-copy`, `save-overwrite`, `graph-load`, `graph-view`) changed to
`{filename:path}`, since an imported file's name (`imported/foo.scd`) contains a `/`
that FastAPI's default path-parameter converter won't match. Frontend's URL-building
also had to switch from a blanket `encodeURIComponent` (which turns `/` into `%2F`) to
per-segment encoding that keeps the `/` literal.

Covered by `tests/test_import_api.py` (upload -> tree/validate work end-to-end,
unsupported extension rejected, name collision disambiguated) using FastAPI's
TestClient against a tmp_path-isolated `FILES_DIR`.

### Bug fix: real-world SCD file import rejected with 413 (2026-11-10)
User-reported: "SCD file import is not working". `tests/test_import_api.py` only
exercised the FastAPI app directly (bypassing the dockerized reverse-proxy), so it
missed that nginx's default `client_max_body_size` (1 MB) was rejecting the upload
before it ever reached `api-gateway` -- both real fixture files are over that
(MAYZAN ~3 MB, DTech26 ~2.7 MB), while the import tests and my own earlier manual
curl check both only used the 1 KB `project.scd`. Fixed with
`client_max_body_size 100m` in `services/reverse-proxy/nginx.conf`. Re-verified by
importing the actual MAYZAN and DTech26 files (not a small fixture) through the real
proxy on port 8080, both now 200 OK. This class of bug -- correct at the FastAPI-app
level, broken only through the real nginx layer -- isn't caught by pytest at all;
it needs an actual `docker compose up` + request-through-the-proxy check, which the
plan's verification section already calls for as a standing gate.

## Left to do

- **Phase 1 — Explorer** (remaining): DataTypeTemplates browser with "used by" back-links.
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
