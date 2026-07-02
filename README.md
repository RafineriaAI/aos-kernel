# AOS Kernel

Public demonstrator version: `0.1.0`

AOS Kernel is a model-agnostic runtime assurance kernel. It converts bounded
signals into deterministic operational decisions with replayable evidence.

```text
signal -> policy -> PASS / WARN / BLOCK -> JSONL record -> SHA-256 hash
```

This repository is the curated public kernel release surface. It contains the
reference kernel, a minimal CLI, Trusted Output v0, Lean proof surface, contract
tests, and compact evidence examples needed to inspect the public demonstrator.

Workflow products built on top of the kernel live separately, for example
[RafineriaAI/aos-workflow-gate](https://github.com/RafineriaAI/aos-workflow-gate).

## What It Does

AOS does not replace scanners, guardrails, reviewers, operators, or final
decision-makers. It sits after upstream tools and before downstream workflow use.

```text
scanner / CI / evaluation signal -> AOS Kernel -> decision + evidence
```

| Kernel capability | Public artifact |
| --- | --- |
| Deterministic PASS/WARN/BLOCK decision | `core/aos_public_core.py` |
| Replayable evidence packet | `build_signal_evidence()` and tests |
| Integrity anchor | SHA-256 digests in evidence and Trusted Output v0 |
| Tamper detection | `verify_signal_evidence()` and `aos trust verify` |
| Abstract formal surface | `lean/AOSPublicCore.lean` |
| Publication boundary | `SCOPE_OF_PROOF.md`, `COMMERCIAL_BOUNDARY.md` |

## Try It

```bash
python -m pip install -e .[dev]
aos demo --output-dir .tmp/aos-demo
```

Expected output:

```text
AOS demo completed.
Verdict: WARN
Decision: REVIEW_REQUIRED
Signals: 3
Evidence: .tmp/aos-demo/check-record.jsonl
Summary: .tmp/aos-demo/check-summary.md
```

Verify the unsigned Trusted Output wrapper:

```bash
aos trust emit \
  --record .tmp/aos-demo/check-record.jsonl \
  --output .tmp/aos-demo/trusted-output.json

aos trust verify \
  --input .tmp/aos-demo/trusted-output.json \
  --record .tmp/aos-demo/check-record.jsonl
```

Current public verification status:

```text
signature_status: UNSIGNED_NOT_OFFICIAL
official_aos_output: false
```

That is expected. Public Trusted Output v0 is structure-checkable and
record-checkable, but not an official signed RafineriaAI/AOS verdict.

## Validate

```bash
python tools/run_validation_gate.py --standard --skip-install
```

The standard gate runs formatting/lint checks, type checks, tests, integrity
verification, and the public Lean surface build when Lean is available.

## What This Proves

The public kernel demonstrates that a bounded input can be converted into a
stable decision and replayable evidence record, and that tampering with the
record or wrapper is detectable by the included verifiers.

It does not prove production readiness, clinical or regulated-use readiness,
security of a target repository, absence of vulnerabilities, compliance, SLA,
commercial ROI, or Python-Lean refinement correctness.

## Repository Boundary

RafineriaAI is the publishing brand and ownership boundary. AOS is the kernel.
Products are concrete applications built on top of that kernel.

This repository is source-available and proprietary. It intentionally excludes
private production policies, calibration logic, enterprise integrations,
signing keys, deployment hardening, customer workflows, and commercial scoring.

## Files

| Path | Purpose |
| --- | --- |
| `core/` | Reference kernel implementation |
| `aos_cli/` | Minimal CLI and Trusted Output v0 utilities |
| `lean/` | Abstract public formal surface |
| `tests/` | Contract and tamper-detection tests |
| `examples/reports/` | Sanitized replay example |
| `tools/run_validation_gate.py` | Canonical local validation entrypoint |
| `evidence/integrity_manifest.json` | Public integrity manifest |

## License

This repository is published under a proprietary demonstrator notice. Viewing
the repository does not grant rights to copy, modify, distribute, host,
commercialize, or create derivative works without written permission.

See [LICENSE](LICENSE) and [NOTICE](NOTICE).