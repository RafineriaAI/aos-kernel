# Integration Boundary

This repository exposes the AOS Kernel as a minimal local package and CLI.

Use it when you need to inspect the kernel contract:

```bash
python -m pip install -e .[dev]
aos demo --output-dir .tmp/aos-demo
aos trust verify --input examples/reports/public-replay-trusted-output.json --record examples/reports/public-replay-record.jsonl
```

Product-level workflow integration belongs in a product repository such as
`RafineriaAI/aos-workflow-gate`. This kernel repository intentionally avoids
customer workflow code, private policies, signing services, license servers, and
enterprise deployment material.