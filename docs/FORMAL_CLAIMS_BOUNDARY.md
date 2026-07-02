# Formal Claims Boundary

This document defines the public scope of the Lean proof surface. It is a
boundary statement, not a full-system verification claim.

## Public Scope

The public Lean layer verifies selected properties of an abstract
`PASS` / `WARN` / `BLOCK` verdict model. The public Python runtime is tested
against the same decision behavior on a bounded demonstrator subset.

This supports a limited statement:

> The public repository demonstrates selected formal properties of a bounded
> verdict model and tests the reference runtime against that model in the public
> demonstrator.

## What Is Covered

- abstract verdict behavior;
- deterministic `PASS` / `WARN` / `BLOCK` structure;
- selected interval-boundary properties;
- abstract fail-closed behavior for incomplete or invalid structured input;
- audit-ready predicates over abstract records;
- public boundary predicates that explicitly do not claim Python-Lean
  refinement, implementation correctness, or deployment assurance;
- bounded runtime tests for the public Python reference implementation.

`jsonInvalidInputBlocks` is an abstract control-model property. The Python
reference parser may reject malformed or out-of-contract input before evidence
generation; that rejection path is not a Python-Lean refinement claim.

## Sufficiency Boundary

| Claim | Current Lean surface |
| --- | --- |
| Abstract verdict-integrity claim | Sufficient for selected invariants |
| Runtime equivalence claim | Not sufficient |
| Signal-extraction correctness claim | Not sufficient |
| Real-world effectiveness claim | Not sufficient |
| Production or regulated-use claim | Not sufficient |

The Lean target is a formal control-model artifact. It is valuable because it
removes ambiguity from the published verdict contract. It should not be used as
the main evidence that AOS improves model behavior, scanner quality, workflow
security, or production outcomes.

## Current Build Quality Gate

The curated repository CI runs the standard validation gate:

```bash
python tools/run_validation_gate.py --standard --skip-install
```

That gate currently executes:

```bash
ruff check .
mypy adapters aos_cli core tests tools
pytest
python tools/verify_public_integrity.py
lake build AOSPublicCore
```

`lake build AOSPublicCore` builds the public Lean package declared in
`lakefile.lean`, including `AOSPublicCore`, `AOSEnvironmentModel`, and
`AOSAxiomAudit`. `AOSAxiomAudit` prints theorem dependency information during
the Lean build.

The current curated CI does not run external proof checkers beyond the Lean package build. Additional independent proof-checking may be future hardening, but it is not part of the current public CI claim.

## What Is Not Covered

- full Python-to-Lean refinement;
- arbitrary floating-point behavior;
- JSON/IO/security/key-management correctness;
- correctness of model-output hashes beyond the public runner checks;
- policy calibration or threshold validity;
- semantic truth of model outputs or retrieved evidence;
- deployment, concurrency, availability, or production security;
- domain, regulatory, financial, or safety approval;
- end-to-end product correctness.

## Safe Public Wording

Use:

> Lean verifies selected properties of the abstract public verdict model.

Avoid:

> The AOS system is formally verified.

Use:

> The public tests check bounded correspondence between the reference runtime
> and the public verdict model.

Avoid:

> The Lean layer proves production runtime correctness.

## Interpretation

A successful Lean build means that the selected formal target compiles in the
declared environment and emits the public dependency report. It does not, by
itself, prove the correctness of the full system, the quality of domain
policies, or the safety of any deployment.