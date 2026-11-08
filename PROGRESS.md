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

## Left to do

- **Phase 1 — Explorer** (tree view, graph view, validation panel, inline editing,
  save-as-copy/save-overwrite UI with confirmation dialog).
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
