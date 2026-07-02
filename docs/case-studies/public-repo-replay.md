# Public Replay Case Study

This case study shows the curated AOS Kernel output for a committed external
workflow artifact. It is intentionally compact: the kernel repository exposes
the replay record and verification path, not the full product workflow gate.

It is a workflow-evidence fixture. It is not independent validation, a security
audit of the target repository, certification, production readiness, or a
security warranty.

## Source Context

| Field | Value |
| --- | --- |
| Repository | `https://github.com/CERT-Polska/mwdb-core` |
| Commit | `bef7afc4fe5345b24cc396174240a76c10971c9d` |
| Input family | sanitized SARIF-derived evidence record |
| Tool source | `semgrep` |
| Public kernel result | `WARN` |
| Decision | `REVIEW_REQUIRED` |

## Reproduction

After checkout:

```bash
python -m pip install -e .[dev]
aos demo --output-dir .tmp/aos-demo
aos trust verify \
  --input examples/reports/public-replay-trusted-output.json \
  --record examples/reports/public-replay-record.jsonl
```

Expected decision:

```text
Verdict: WARN
Decision: REVIEW_REQUIRED
Finding count: 3
Status: UNSIGNED_NOT_OFFICIAL
Record checked: true
```

## Evidence Artifacts

| Artifact | Path |
| --- | --- |
| Summary | `examples/reports/public-replay-summary.md` |
| JSONL record | `examples/reports/public-replay-record.jsonl` |
| Trusted Output v0 wrapper | `examples/reports/public-replay-trusted-output.json` |

Current Trusted Output status:

```text
schema_version: aos-trusted-output/v0
signature_status: UNSIGNED_NOT_OFFICIAL
official_aos_output: false
```

## Direct Value Shown

- 3 raw finding signals are represented as one workflow decision.
- The decision is recorded as JSONL.
- The record carries a SHA-256 hash.
- The output can be wrapped as unsigned Trusted Output v0.
- The wrapper can be checked against the source JSONL record.
- Sanitized evidence can be shared without publishing target source code.

## Boundary

This case study does not prove that the target repository is secure or insecure.
It does not prove scanner completeness, production readiness, commercial ROI,
certification, compliance, or external validation. It does not replace human
review.

Full workflow-gate execution belongs in a product or pilot surface, not in this
curated kernel repository.