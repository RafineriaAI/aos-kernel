# Public Replay Summary

| Field | Value |
| --- | --- |
| Repository | `https://github.com/CERT-Polska/mwdb-core` |
| Commit | `bef7afc4fe5345b24cc396174240a76c10971c9d` |
| Input | sanitized SARIF-derived evidence record |
| Tool | `semgrep` |
| AOS mode | `demo` |
| Result | `WARN` |
| Decision | `REVIEW_REQUIRED` |
| Findings | `3` |
| Evidence SHA-256 | `98e911708bb1e169b0035fe0f840361cb304499efdbb52f341a9ff55390b4dd6` |

## Recommendation

Review the 3 normalized signal(s) before downstream workflow use.

## Generated Artifacts

| Artifact | Path |
| --- | --- |
| Human summary | `examples/reports/public-replay-summary.md` |
| JSONL record | `examples/reports/public-replay-record.jsonl` |
| Trusted Output v0 wrapper | `examples/reports/public-replay-trusted-output.json` |

## Current Trust Level

```text
schema_version: aos-trusted-output/v0
signature_status: UNSIGNED_NOT_OFFICIAL
official_aos_output: false
```

Unsigned Trusted Output v0 is structure-checkable public evidence. When verified
with the source JSONL record, it also checks record consistency. It is not an
official signed RafineriaAI/AOS verdict.

## Value Shown

- 3 raw scanner-derived signals were converted into one operational decision.
- The decision has a JSONL evidence record.
- The record has a stable SHA-256 hash.
- The wrapper can be checked against the source record.
- The evidence can be shared without publishing target source code.
- The run remains bounded by explicit claim boundaries.

## Boundary

This is a sanitized kernel evidence fixture. It is not independent validation,
certification, a security audit of the target repository, production readiness,
commercial ROI, or a security warranty.
