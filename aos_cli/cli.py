from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Final, cast

from adapters.strict_json import StrictJsonLimits, load_json_object_path
from aos_cli import trusted_output
from core.aos_public_core import build_signal_evidence, parse_signal

VERDICT_INPUT_LIMITS: Final = StrictJsonLimits(
    max_bytes=64 * 1024,
    max_depth=16,
    max_nodes=10_000,
)
DEMO_SIGNAL: Final[dict[str, Any]] = {
    "limit": 9000,
    "metadata_complete": True,
    "score": 8200,
    "signal_id": "demo-signal-001",
    "uncertainty": 700,
    "warn_margin": 1000,
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_json_object(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], load_json_object_path(path, VERDICT_INPUT_LIMITS))


def _write_json(value: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output is None:
        print(text, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")


def demo_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the bundled AOS kernel demo.")
    parser.add_argument("--output-dir", type=Path, default=Path(".tmp/aos-demo"))
    args = parser.parse_args(argv)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = output_dir / "check-summary.md"
    record = output_dir / "check-record.jsonl"

    signal = parse_signal(DEMO_SIGNAL)
    evidence = asdict(build_signal_evidence(signal))
    demo_record = _build_demo_record(evidence)
    _write_demo_record(record, demo_record)
    _write_demo_summary(summary, evidence, demo_record)

    print("AOS demo completed.")
    print(f"Verdict: {evidence['verdict']}")
    print(f"Decision: {demo_record['decision']}")
    print(f"Signals: {demo_record['finding_count']}")
    print(f"Evidence: {record}")
    print(f"Summary: {summary}")
    return 0


def _decision_for_verdict(verdict: object) -> str:
    if verdict == "PASS":
        return "MERGE_ALLOWED"
    if verdict == "WARN":
        return "REVIEW_REQUIRED"
    return "BLOCKED"


def _action_for_verdict(verdict: object) -> str:
    if verdict == "PASS":
        return "allow_downstream_use"
    if verdict == "WARN":
        return "review_required_before_downstream_use"
    return "block_downstream_use"


def _build_demo_record(evidence: dict[str, Any]) -> dict[str, Any]:
    verdict = evidence["verdict"]
    signal_input = cast(dict[str, Any], evidence["input"])
    input_digest = str(evidence["input_digest"]).removeprefix("sha256:")
    finding_count = 0 if verdict == "PASS" else 1
    record: dict[str, Any] = {
        "schema_version": "aos-developer-workflow-record/v1",
        "mode": "demo",
        "source_kind": "aos_demo_signal",
        "source_ref": f"aos://demo/{evidence['signal_id']}",
        "source_commit": str(evidence["audit_id"]).removeprefix("sha256:")[:40],
        "base_commit": "not_applicable",
        "tool": "aos-kernel-demo",
        "adapter": "aos_demo_signal_adapter",
        "adapter_version": "aos-kernel-demo-record/v1",
        "input_format": "aos-demo-signal/v1",
        "input_sha256": input_digest,
        "aos_verdict": verdict,
        "decision": _decision_for_verdict(verdict),
        "finding_count": finding_count,
        "reason": evidence["reason"],
        "action": _action_for_verdict(verdict),
        "status": "ok",
        "decision_hash": trusted_output.sha256_hex(
            {
                "policy_id": evidence["policy_id"],
                "policy_version": evidence["policy_version"],
                "reason": evidence["reason"],
                "verdict": verdict,
            }
        ),
        "kernel_evidence": evidence,
        "signal_score": signal_input["score"],
        "signal_uncertainty": signal_input["uncertainty"],
        "signal_limit": signal_input["limit"],
        "signal_warn_margin": signal_input["warn_margin"],
    }
    record["record_sha256"] = trusted_output.sha256_hex(record)
    return record


def _write_demo_record(path: Path, record: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_demo_summary(
    path: Path,
    evidence: dict[str, Any],
    record: dict[str, Any],
) -> None:
    signal_input = cast(dict[str, Any], evidence["input"])
    path.write_text(
        "\n".join(
            [
                "# AOS Demo Summary",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Signal | `{evidence['signal_id']}` |",
                f"| Verdict | `{evidence['verdict']}` |",
                f"| Decision | `{record['decision']}` |",
                f"| Score | `{signal_input['score']}` |",
                f"| Uncertainty | `{signal_input['uncertainty']}` |",
                f"| Limit | `{signal_input['limit']}` |",
                f"| Warn margin | `{signal_input['warn_margin']}` |",
                f"| Evidence digest | `{evidence['input_digest']}` |",
                "",
                "## Reason",
                "",
                str(evidence["reason"]),
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def verdict_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate one bounded AOS demo signal."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        signal = parse_signal(_load_json_object(args.input))
        evidence = asdict(build_signal_evidence(signal))
        _write_json(evidence, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


def validate_main(argv: list[str] | None = None) -> int:
    script = _repo_root() / "tools" / "run_validation_gate.py"
    result = subprocess.run([sys.executable, str(script), *(argv or [])], check=False)
    return int(result.returncode)


def _help() -> str:
    return """AOS Kernel

Usage:
  aos demo [--output-dir DIR]
  aos verdict --input signal.json [--output evidence.json]
  aos trust emit --record record.jsonl --output trusted-output.json
  aos trust verify --input trusted-output.json [--record record.jsonl]
  aos validate [--quick|--standard|--full] [--skip-install]

Boundary:
  This is a public kernel demonstrator, not a production SDK, certification,
  security audit, compliance assessment, or official signed verdict service.
"""


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] in {"-h", "--help"}:
        print(_help())
        return 0
    command, rest = args[0], args[1:]
    if command == "demo":
        return demo_main(rest)
    if command == "verdict":
        return verdict_main(rest)
    if command == "trust":
        return trusted_output.main(rest)
    if command == "validate":
        return validate_main(rest)
    print(f"ERROR: unknown command: {command}", file=sys.stderr)
    print(_help(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
