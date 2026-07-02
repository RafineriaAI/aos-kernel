from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from aos_cli import trusted_output
from core.aos_public_core import build_signal_evidence, parse_signal


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    return payload


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

    root = _repo_root()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = output_dir / "check-summary.md"
    record = output_dir / "check-record.jsonl"
    source_summary = root / "examples" / "reports" / "public-replay-summary.md"
    source_record = root / "examples" / "reports" / "public-replay-record.jsonl"
    shutil.copyfile(source_summary, summary)
    shutil.copyfile(source_record, record)

    print("AOS demo completed.")
    print("Verdict: WARN")
    print("Decision: REVIEW_REQUIRED")
    print("Signals: 3")
    print(f"Evidence: {record}")
    print(f"Summary: {summary}")
    return 0


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