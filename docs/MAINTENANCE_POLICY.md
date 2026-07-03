# Maintenance Policy

After `v0.1.1`, `aos-kernel` is in scope-locked maintenance mode.

This does not make the repository inactive. It means the public kernel surface is
kept small, auditable, and stable while workflow-product development moves to
`RafineriaAI/aos-workflow-gate`.

## Allowed Changes

Changes in this repository should preserve the curated public kernel boundary.
Allowed work includes:

- kernel bug fixes and narrowly scoped edge-case hardening;
- tests for deterministic verdicts, evidence integrity, tampering, rollback,
  fork, and impersonation resistance;
- sanitized evidence fixtures and integrity manifest updates;
- Lean/formal-surface maintenance for the abstract verdict model;
- CI, Dependabot, validation-gate, and release-governance hygiene;
- documentation that clarifies or narrows public claims.

## Out of Scope

Do not add workflow-product behavior to `aos-kernel`. Out-of-scope work includes:

- CI, PR, scanner, repository, or AI-agent workflow adapters;
- commercial orchestration, scoring, routing, or policy packs;
- product dashboards, customer workflow integrations, or deployment hardening;
- effectiveness benchmarks beyond the current synthetic fixture set;
- production readiness, compliance, official signing, SLSA, SBOM, or security
  audit claims without separately audited infrastructure.

## Where New Work Goes

Workflow-product experiments and user-facing workflow gates belong in
`RafineriaAI/aos-workflow-gate` unless the change is required to preserve the
public kernel contract.

Future `aos-kernel` releases should be patch-sized by default. If a change would
expand the public surface, treat it as a release-governance decision before it is
implemented.