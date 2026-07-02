# Public Replay Summary

| Field | Value |
| --- | --- |
| Repository | `https://github.com/CERT-Polska/mwdb-core` |
| Commit | `bef7afc4fe5345b24cc396174240a76c10971c9d` |
| Input | committed SARIF sample |
| Tool | `semgrep` |
| AOS mode | `gate` |
| Result | `WARN` |
| Decision | `REVIEW_REQUIRED` |
| Findings | `3` |
| Evidence SHA-256 | `67ae06eb4a1a71bb5e07874902adf99f8ad7d876ab91e66b59de2528f6ff1551` |

## Recommendation

Review the 3 normalized signal(s) before merge, deployment, or downstream
workflow use.

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

Unsigned Trusted Output v0 is structure-checkable public evidence. When
verified with the source JSONL record, it also checks record consistency. It is
not an official signed RafineriaAI/AOS verdict.

## Value Shown

- 3 raw scanner findings were converted into one operational decision.
- The decision has a JSONL evidence record.
- The record has a stable SHA-256 hash.
- The evidence can be shared without publishing target source code.
- The run remains bounded by explicit claim boundaries.

## Pilot Use

A comparable pilot should provide a pinned commit and a scanner, CI, or
agent-output artifact. The external shareable result should be sanitized
evidence: summary, decision, record hash, trust status, and claim boundary.

## Boundary

This is a workflow adapter proof. It is not independent validation,
certification, a security audit of the target repository, production readiness,
commercial ROI, or a security warranty.
