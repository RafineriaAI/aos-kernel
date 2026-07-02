# Scope Of Proof

This repository is a public demonstrator of the AOS runtime assurance pattern.
Its proof surface is useful, but intentionally narrow.

For claim-level interpretation, see
[Formal Claims Boundary](docs/FORMAL_CLAIMS_BOUNDARY.md).

## Proven

- deterministic abstract verdict logic in the public Lean proof surface
- explicit policy evaluation in the public interval-gate demonstrator
- audit digest generation for demonstrator decisions
- reproducible JSON evidence for the current synthetic benchmark set

## Formal Sufficiency

The current Lean surface is sufficient for one narrow claim:

```text
selected properties of the abstract public verdict model are formally checked
in the pinned Lean environment
```

It is not sufficient for a system-level effectiveness or production claim.
Those claims would require additional artifacts outside the current proof
surface: runtime refinement, parser and IO correctness, signal-extraction
validation, representative data, baseline comparisons, and operational tests.

The public integrity check also rejects Lean gap terms in committed Lean
sources. This prevents placeholder proofs from being published as verified
artifacts.

## Numeric Precision Boundary

The public Lean proof surface covers abstract integer verdict logic. Production
runtime paths should use canonical fixed-point signals or an explicitly bounded
floating-point error model before verdict evaluation.

IEEE-754 behavior, JSON numeric parsing, rounding modes, and platform runtime
semantics are outside the current public proof surface. Near-boundary cases
should route to `WARN` when numeric error could change the verdict.

## Demonstrated

- model-output signal to `PASS` / `WARN` / `BLOCK` decision flow
- SHA-256-linked audit trace in the public demonstrator
- domain-neutral control-layer shape
- clean-room repeatability using only the public repository contents

## Not Claimed

- Python-to-Lean refinement
- full Python numeric runtime behavior
- full Int/Float correspondence between code and proof artifacts
- production SDK completeness
- production security or deployment readiness
- domain validation or regulated-use approval
- regulatory approval or safety approval
- external validation or independent assessment
- product performance in deployment environments
- production-system completeness
- production calibration, load performance, domain-adapter quality, deployment
  economics, or operational readiness
- materials outside this public demonstrator

The public repository should be read as a technical credibility signal and
repeatable runtime assurance demonstrator.
