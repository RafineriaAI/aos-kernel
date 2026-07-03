# Validation Gates

The canonical local validation entrypoint is:

```bash
python tools/run_validation_gate.py --standard --skip-install
```

Validation levels:

| Mode | Purpose |
| --- | --- |
| `quick` | integrity + tests |
| `standard` | ruff, mypy, tests, integrity, Lean build if available |
| `full` | same as standard for the curated public kernel |

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