# Contributing

This repository is intentionally limited. Contributions, if accepted, must
preserve the public-demonstrator boundary and the proprietary rights reserved in
[LICENSE](LICENSE) and [NOTICE](NOTICE).

## Contribution Status

External contributions are not accepted unless the maintainer has approved them
in advance and any required contributor agreement, copyright assignment, or
inbound license is complete in writing.

Unsolicited pull requests may be closed without review. Opening an issue,
comment, fork, clone, or pull request does not create an implied license to the
AOS Kernel, documentation, product direction, or unpublished implementation
material.

By submitting material, you represent that you have the right to submit it and
that it does not contain confidential, employer-owned, third-party,
export-controlled, regulated, or otherwise controlled material unless written
clearance has already been obtained.

## Do Not Submit

Do not submit:

- full AOS Core or production-system code;
- private policies, scoring logic, calibration methods, or customer adapters;
- signing keys, license-server material, deployment secrets, local paths, or
  internal logs;
- model weights, datasets, labels, checkpoints, ONNX/TensorRT engines,
  safetensors, PT/PTH files, or model binaries;
- controlled customer data, regulated data, private scanner output, or private
  findings;
- claims that this public demonstrator is production-ready, certified,
  compliant, externally validated, or sufficient for autonomous high-risk use.

## Required Checks

Run the current curated-kernel validation path before submitting changes:

```bash
python -m pip install -e .[dev]
ruff check .
mypy adapters aos_cli core tests tools
pytest
python tools/verify_public_integrity.py
aos demo --output-dir .tmp/aos-demo
aos trust verify --input examples/reports/public-replay-trusted-output.json --record examples/reports/public-replay-record.jsonl
python tools/run_validation_gate.py --standard --skip-install
```

If Lean is available, the standard validation gate also builds the public Lean
surface:

```bash
lake build AOSPublicCore
```

Do not add product-level workflow automation, pilot verifiers, production hardening checks, or benchmark suites to this curated kernel repository unless they are explicitly promoted into the public kernel contract.

Keep documentation, evidence, claims, and public positioning inside the
demonstrator boundary.