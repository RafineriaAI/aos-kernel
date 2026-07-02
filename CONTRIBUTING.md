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
AOS Core, documentation, or product direction.

By submitting material, you represent that you have the right to submit it and
that it does not contain confidential, employer-owned, third-party,
export-controlled, regulated, or otherwise
controlled material unless written clearance has already been obtained.

## Do Not Submit

Do not submit:

- full AOS Core code
- production-system implementation material
- specialist-system material
- model weights, datasets, labels, checkpoints, ONNX/TensorRT engines,
  safetensors, PT/PTH files, or model binaries
- generated claim bundles
- deployment secrets, local paths, internal logs, or controlled data
- material that requires controlled disclosure review

Do not add claims that this public demonstrator is approved, externally
validated, sufficient for autonomous high-risk use, production deployment-ready,
regulatory compliant, or externally ranked.

## Required Checks

Run before submitting changes:

```bash
python -m pip install -e .[dev]
python tools/verify_json_safety.py
ruff check .
mypy core benchmarks adapters aos_cli tools
python tools/run_pytest_suite.py --profile full
python benchmarks/run_benchmarks.py --check
python benchmarks/run_llm_assurance_benchmark.py --check
python benchmarks/run_llm_hard_case_benchmark.py --check
python benchmarks/run_operational_control_replay.py --check
python benchmarks/run_operational_stability_check.py --check
python benchmarks/run_vulnerability_risk_gate.py --check
python benchmarks/run_agent_action_gate.py --check
python benchmarks/run_public_agentic_workflow_replay.py --check
python benchmarks/run_ci_assurance_replay.py --check
python benchmarks/run_production_shadow_gate.py --check
python benchmarks/run_adoption_workflow_replay.py --check
python benchmarks/run_comparative_assurance_benchmark.py --check
python benchmarks/export_external_assurance_inputs.py --check
python benchmarks/import_inspect_ai_results.py --check
python benchmarks/import_garak_results.py --check
python benchmarks/import_sarif_results.py --self-check
python benchmarks/run_ragtruth_public_benchmark.py --check
python benchmarks/run_public_assurance_evaluation_suite.py --check
python benchmarks/profile_arithmetic.py
python benchmarks/run_adapters_check.py
python benchmarks/run_policy_adapter_stress.py --check
python benchmarks/run_input_signal_quality_check.py
python tools/verify_manifest_completeness.py
python tools/verify_spec_drift.py
python tools/verify_claim_boundaries.py
python tools/verify_json_artifacts.py
python tools/verify_deterministic_serialization.py
python tools/verify_policy_compatibility.py
python tools/verify_trust_boundaries.py
python tools/verify_zero_trust_ci.py
python tools/verify_evidence_dag_regression.py
python tools/verify_claim_bound_isolation.py
python tools/verify_validation_gate_inventory.py
python tools/verify_assurance_sequence.py
python tools/verify_proprietary_claim_leak.py
python tools/verify_public_provenance.py
python tools/verify_substrate_contract.py
python tools/verify_production_evidence_gate.py
python tools/verify_regulatory_evidence_boundary.py
python tools/verify_commercial_utility_evidence.py
python tools/verify_adoption_potential_evidence.py
python tools/verify_vulnerability_risk_gate.py
python tools/verify_agent_action_gate.py
python tools/verify_public_agentic_workflow_replay.py
python tools/verify_ci_assurance_replay.py
python tools/verify_production_shadow_gate.py
python tools/verify_adoption_workflow_replay.py
python tools/verify_comparative_assurance_benchmark.py
python tools/verify_external_assurance_exports.py
python tools/verify_inspect_ai_result_import.py
python tools/verify_garak_result_import.py
python tools/verify_external_guardrail_result_import.py
python tools/verify_sarif_result_import.py
python tools/verify_executable_diligence_matrix.py
python tools/verify_external_assurance_surface.py
python tools/verify_ci_assurance_gate.py
python tools/run_reviewer_verification.py --self-check
python tools/run_external_shadow_workflow.py --self-check
python tools/verify_operational_stability_evidence.py
python tools/verify_public_assurance_evaluation_suite.py
python tools/run_api_contract_check.py --max-examples 100
python tools/verify_doc_references.py
python tools/verify_evidence_gap_register.py
python tools/verify_public_integrity.py
lake build AOSPublicCore AOSEnvironmentModel AOSAxiomAudit
python tools/verify_lean_axioms.py
python tools/verify_public_invariants.py
lake env leanchecker --fresh AOSAxiomAudit
```

Optional local falsification check:

```bash
python -m mutmut run
```

Keep documentation, evidence, claims, benchmark outputs, and public positioning
within the demonstrator boundary.

To execute the complete canonical command inventory locally with fail-fast
behavior, run `python tools/run_validation_gate.py`.
