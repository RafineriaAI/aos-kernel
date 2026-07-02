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

The gate does not update the integrity manifest, regenerate evidence, or extend
public claims.