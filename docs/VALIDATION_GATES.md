# Validation Gates

The canonical local validation entrypoint is:

```bash
python tools/run_validation_gate.py --standard --skip-install
```

Validation levels:

| Mode | Purpose |
| --- | --- |
| `quick` | integrity + tests |
| `standard` | ruff, mypy, tests, Trusted Output guard, integrity, Lean build if available |
| `full` | same as standard for the curated public kernel |


CI-only hardening workflows:

| Workflow | Purpose |
| --- | --- |
| `aos-kernel-codeql.yml` | CodeQL analysis for Python source and workflow-triggered uploads |
| `aos-kernel-supply-chain.yml` | actionlint, gitleaks, and OpenSSF Scorecard checks |

These external checks are pinned at full commit SHA in GitHub Actions, with
exact Go patch versions for Go-installed tools. They are not required as local
developer dependencies for emergency kernel fixes.

Release-surface audit precheck:

```bash
python tools/audit_precheck.py
```

Before preparing a future release tag, use the release form:

```bash
python tools/audit_precheck.py --release-version 0.1.1 --check-remote
```

The gate does not update the integrity manifest, regenerate evidence, or extend
public claims.

The audit precheck is local evidence only. It does not certify compliance,
production readiness, official signing, or repository-hosted branch protections.