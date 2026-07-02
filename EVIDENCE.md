# Evidence

This curated repository contains a compact public evidence surface for the AOS
Kernel.

| Evidence | Location |
| --- | --- |
| Reference decision logic | `core/aos_public_core.py` |
| Contract tests | `tests/test_aos_public_core.py` |
| Trusted Output v0 tests | `tests/test_trusted_output.py` |
| Example replay record | `examples/reports/public-replay-record.jsonl` |
| Integrity manifest | `evidence/integrity_manifest.json` |
| Abstract Lean model | `lean/AOSPublicCore.lean` |

The evidence shows deterministic conversion of bounded signals into
`PASS/WARN/BLOCK`, replayable JSON records, hash anchors, and tamper detection.
It does not prove production readiness, compliance, external validation, or
runtime-to-formal refinement.