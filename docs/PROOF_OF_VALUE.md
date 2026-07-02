# Kernel Proof Of Value

This is the shortest practical path for evaluating the public AOS Kernel as a
bounded decision-and-evidence layer.

Current stage:

```text
public kernel demonstrator -> bounded input -> PASS/WARN/BLOCK -> replayable evidence
```

The public kernel repository should be evaluated as a deterministic decision
kernel, not as a scanner, model, agent framework, security audit,
certification, or production deployment.

## What To Run First

Install the local package and run the bundled offline demo:

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

The useful shape is:

```text
bounded artifact -> PASS/WARN/BLOCK -> summary -> JSONL record -> SHA-256
```

## Verify The Evidence Wrapper

The public Trusted Output v0 wrapper is unsigned. It is still useful because it
can be checked against the source JSONL record:

```bash
aos trust verify \
  --input examples/reports/public-replay-trusted-output.json \
  --record examples/reports/public-replay-record.jsonl
```

Expected verification status:

```text
Status: UNSIGNED_NOT_OFFICIAL
Official: false
Record checked: true
```

## Evaluate One Custom Signal

A minimal signal can be evaluated with the reference kernel contract:

```json
{
  "signal_id": "local-signal-001",
  "score": 8000,
  "uncertainty": 1000,
  "limit": 9000,
  "warn_margin": 1000,
  "metadata_complete": true
}
```

Run:

```bash
aos verdict --input signal.json --output evidence.json
```

The output is a replayable evidence packet containing the verdict, reason,
input digest, audit id, policy id, and explicit claim boundary.

## What To Measure

For one bounded workflow artifact, record:

| Metric | Why it matters |
| --- | --- |
| time to first verdict | integration friction |
| verdict | decision shape |
| finding or signal count | review size |
| record SHA-256 availability | integrity anchor |
| replay success | reproducibility |
| verification status | whether the output is official, unsigned, or tampered |
| operator notes | practical fit and false-review pressure |

## Current Public Proof

This repository includes a sanitized replay record derived from a committed
third-party SARIF workflow sample from `CERT-Polska/mwdb-core`. In the curated
kernel repository, the SARIF import path itself is not exposed as the primary
interface; the committed output is used as a compact evidence fixture.

The fixture demonstrates:

- deterministic `WARN` / `REVIEW_REQUIRED` output;
- JSONL evidence;
- record hash;
- unsigned Trusted Output v0 wrapper;
- replayable verification against the source record.

## Stronger Next Proof

The next useful evidence step should happen in a product or pilot surface, such
as `RafineriaAI/aos-workflow-gate`, using a real workflow artifact and a pinned
commit. This kernel repository should remain focused on the kernel contract and
its minimal reproducible evidence.

## Boundaries

This proof-of-value path does not establish:

- production readiness;
- customer adoption;
- willingness to pay;
- compliance or certification;
- target-repository security;
- general AOS effectiveness;
- correctness of the upstream model, scanner, CI system, or agent;
- Python-Lean refinement correctness.

It establishes only whether the public AOS Kernel pattern is executable,
inspectable, replayable, and useful enough to evaluate in a bounded workflow.