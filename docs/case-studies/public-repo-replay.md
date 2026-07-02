# Public Repo Replay Case Study

This case study shows the public AOS workflow gate on a committed scanner
artifact from an external public repository.

It is a workflow adapter proof. It is not independent validation, a security
audit of the target repository, certification, production readiness, or a
security warranty.

## Target

| Field | Value |
| --- | --- |
| Repository | `https://github.com/CERT-Polska/mwdb-core` |
| Commit | `bef7afc4fe5345b24cc396174240a76c10971c9d` |
| Input | committed SARIF sample |
| Tool source | `semgrep` |
| Mode | `gate` |

## Reproduction

After checkout:

```bash
python -m pip install -e .
aos gate \
  --sarif docs/public-evidence/runs/mwdb-core-bef7afc-gate/gate.sarif \
  --source-commit bef7afc4fe5345b24cc396174240a76c10971c9d \
  --output-dir .tmp/aos-public-repo-replay
```

Expected decision:

```text
Result: WARN
Decision: REVIEW_REQUIRED
Finding count: 3
```

## Generated Artifacts

| Artifact | Path |
| --- | --- |
| Summary | `examples/reports/public-replay-summary.md` |
| JSONL record | `examples/reports/public-replay-record.jsonl` |
| Trusted Output v0 wrapper | `examples/reports/public-replay-trusted-output.json` |
| Source SARIF | `docs/public-evidence/runs/mwdb-core-bef7afc-gate/gate.sarif` |

Current Trusted Output status:

```text
schema_version: aos-trusted-output/v0
signature_status: UNSIGNED_NOT_OFFICIAL
official_aos_output: false
```

## Direct Value Shown

- 3 raw scanner findings are converted into one workflow decision.
- The decision is recorded as JSONL.
- The record carries a SHA-256 hash.
- The output can be wrapped as unsigned Trusted AOS Output.
- Sanitized evidence can be shared without publishing target source code.

## Pilot Use

A first pilot can use this pattern with a pinned commit and an existing SARIF,
CI, or agent-output artifact. The external artifact to share is the sanitized
summary plus JSONL record hash, not private source code or confidential scanner
output.

Recommended pilot intake fields:

- repository or local artifact type;
- pinned commit;
- tool used;
- AOS verdict and decision;
- record SHA-256;
- execution environment;
- permission boundary.

## Boundaries

This case study does not prove that the target repository is secure or insecure.
It does not prove scanner completeness, production readiness, commercial ROI,
certification, compliance, or external validation. It does not replace human
review.
