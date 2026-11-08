# validation-sidecar

Thin HTTP wrapper around RiseClipse's `RiseClipseValidatorSCL.jar`
(`POST /validate?filename=...` with the raw SCL file as the request body;
`GET /health`).

## Known follow-ups (not yet done, tracked here on purpose)

1. **OCL semantic rules are not populated.** `rules/ocl/` and `rules/nsd/`
   are empty by default, so the service currently only reports what the
   RiseClipse jar can say about a file with no `.ocl`/`.nsd` files loaded
   (structural parsing only — no IEC 61850-7-x LN-class/CDC conformance
   checks). Populate those two directories from RiseClipse's published
   constraint set (see https://riseclipse.github.io/downloads and
   https://github.com/riseclipse/riseclipse-ocl-constraints-scl2003) to turn
   on real OCL semantic validation; no code change is needed, the wrapper
   already passes both directories to the validator whenever they're
   non-empty, and reports `oclRulesApplied`/`nsdRulesApplied` in its
   response either way.
2. **No XSD schema is vendored into this repo.** The official SCL XSD set
   is distributed under IEC's own EULA (confirmed via the `compas-scl-xsd`
   repository's disclaimer, which notes some files are CC-EULA-licensed) —
   not a permissive open-source license — so it is not bulk-copied into this
   repository. To enable the preliminary XSD pass, obtain `SCL.xsd` + its
   cooperating schemas yourself (e.g. the `compas-scl-xsd` GitHub Packages
   artifact, subject to its own license) and set `SCL_XSD_SCHEMA` to the
   mounted path. Until then, structural well-formedness is still checked by
   the Python parser in `api-gateway` (XML-syntax errors surface as a 422
   from `POST /files/{name}/parse`), just not full XSD-schema conformance.
3. **Pre-launch legal checklist item** (per the plan's licensing note):
   `riseclipse/riseclipse-validator-scl` is EPL-2.0 (not GPLv3 — that
   concern is about libiec61850 in the Simulator Service, a separate
   component), so no process-isolation argument is needed for this service
   specifically.
