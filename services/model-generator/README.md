# model-generator

Placeholder service for Phase 0/1/2. `GET /health` only; `POST /generate`
returns `501 not_implemented`.

Phase 3 implements the real behavior here: wrap libiec61850's
`genconfig.jar` (dynamic/config-file model generator) to turn a single
chosen IED's SCL subset into a `.cfg` model file for the Simulator Service,
per the technical plan's component 6.
