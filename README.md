# SCD-POC — SCL Explorer, Agent Mode, Auto-Simulator

Implements the technical plan at
[plans/scl-explorer-agent-simulator-technical-plan.md](plans/scl-explorer-agent-simulator-technical-plan.md).
This README covers **Phase 0 — Foundations**, the first phase built.

## What's built (Phase 0)

| Component | Status |
|---|---|
| SCL parser/serializer (Python, lxml) | Done — parses Header/Substation/IED/Communication/DataTypeTemplates, resolves `lnType -> LNodeType -> DO -> DOType -> DA`, retains `<Private>` blobs untouched, byte-identical no-op round trip |
| Custom validation rules | Done — clause 9.2.6 naming uniqueness, duplicate IP/MAC per SubNetwork, empty/misconfigured control blocks, dangling `lnType`/`ExtRef` references, missing-Substation-in-an-.scd |
| Validation sidecar (RiseClipse wrapper) | Done, scoped — structural/XSD pass works; OCL semantic rules need rule files populated (see below) |
| Neo4j knowledge graph ingestion | Done — full node/edge schema from the research report (containment, `INSTANCE_OF`/`TYPED_AS`, `PUBLISHES`/`HAS_MEMBER`, `SUBSCRIBES_TO`/`REFERENCES` with dangling refs flagged not dropped, `ON`/`ASSOCIATED_WITH`) |
| FastAPI gateway | Done — parse/validate/graph-load/save endpoints, proxies validation-sidecar |
| `docker-compose.yml` (core profile) | Done — all 7 core services verified to come up cleanly together |
| model-generator, frontend | Scaffolded as placeholders (real work is Phase 3 and Phase 1 respectively) |

Phase 1 (Explorer tree/graph/editor UI), Phase 2 (Agent mode), and Phase 3
(Simulator) are not built yet.

## Running it

```bash
cp .env.example .env
# edit .env: set a real NEO4J_PASSWORD at minimum
docker compose up -d
```

Open http://localhost:8080 — the placeholder frontend shows api-gateway
health and the files found under `SCD_FILES_HOST_DIR` (defaults to this
repo's own `Resources/` folder).

API (behind the reverse proxy at `/api`, or directly on the api-gateway
container at :8000):

```bash
curl -X POST "http://localhost:8080/api/files/project.scd/parse"
curl "http://localhost:8080/api/files/project.scd/validate"
curl -X POST "http://localhost:8080/api/files/project.scd/graph-load"
curl "http://localhost:8080/api/graph/subnetworks/WA1/ieds"
```

`docker compose down` to stop; add `-v` to also drop the Neo4j volume.

## Tests

```bash
cd services/api-gateway
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m pytest
```

Covers: parser round-trip (no-op save is byte-identical on all four
`Resources/` fixtures) and validation-report snapshots pinned to the two
defects confirmed by hand during planning — MAYZAN's three IEDs sharing
`10.1.150.3`, and DTech26's missing `<Substation>` section.

## Known follow-ups (scoped deliberately, not oversights)

1. **OCL semantic rule files aren't populated** — `services/validation-sidecar/rules/{ocl,nsd}/`
   are empty. The wrapper already uses them whenever non-empty; see that
   service's own README for where to source RiseClipse's published
   constraint set.
2. **No IEC SCL XSD is vendored into this repo.** The official schema set
   is IEC-EULA-licensed, not permissively open-source (confirmed via the
   `compas-scl-xsd` repository's own disclaimer) — not something to
   bulk-copy in without checking that license first. Structural
   well-formedness is still enforced by the Python parser; full XSD-schema
   conformance needs `SCL_XSD_SCHEMA` pointed at a schema you've obtained
   yourself.
3. **`riseclipse/riseclipse-validator-scl`'s published Docker image bundles
   a Java 17 JRE, but its own jar requires Java 21+.** Worked around by
   building the sidecar's own image on `eclipse-temurin:21`, copying only
   the jar out of the upstream image — see
   `services/validation-sidecar/Dockerfile`.
4. **Graph ingestion of a large SCD takes ~10–25s** (tens of thousands of
   nodes/edges) even with the uniqueness-constraint-backed `:Node` label
   trick in `graph/loader.py`; fine within the reverse proxy's 300s
   timeout for this phase, but worth profiling before Phase 2's agent
   starts calling it interactively.
5. **Pre-launch legal checklist item** (per the plan): the Simulator
   Service (Phase 3) embeds GPLv3 libiec61850 and needs real legal sign-off
   on the process-isolation approach before any client shipment. Not a
   Phase 0 blocker.

## Repo layout

```
services/
  api-gateway/        FastAPI gateway: SCL parser/serializer, custom validation, Neo4j loader
  validation-sidecar/ Java HTTP wrapper around RiseClipse's SCL validator
  model-generator/    Placeholder for Phase 3's genconfig.jar wrapper
  frontend/           Placeholder React app (real Explorer UI is Phase 1)
  reverse-proxy/      nginx: routes /api -> api-gateway, / -> frontend
  llm-proxy/          LiteLLM config (used from Phase 2 onward)
Resources/            The four fixture SCD/ICD/CID files used as acceptance tests
plans/                Technical plan
reports/, research_notes/   Background research this plan was built from
```
