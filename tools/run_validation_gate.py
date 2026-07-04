from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

from adapters.strict_json import StrictJsonLimits, load_json_object_path

REPO_ROOT = Path(__file__).resolve().parents[1]
TRUST_VERIFICATION_OUTPUT = REPO_ROOT / ".tmp" / "aos-trust-verification.json"
TRUST_VERIFICATION_COMMAND: Final = (
    "aos trust verify "
    "--input examples/reports/public-replay-trusted-output.json "
    "--record examples/reports/public-replay-record.jsonl "
    "--output .tmp/aos-trust-verification.json"
)
TRUST_VERIFICATION_LIMITS: Final = StrictJsonLimits(
    max_bytes=64 * 1024,
    max_depth=16,
    max_nodes=10_000,
)
EXPECTED_TRUST_VERIFICATION: Final = {
    "status": "UNSIGNED_NOT_OFFICIAL",
    "official_aos_output": False,
    "source_record_checked": True,
}

COMMANDS = {
    "quick": [
        "python tools/verify_public_integrity.py",
        "pytest",
    ],
    "standard": [
        "ruff check .",
        "mypy --no-sqlite-cache adapters aos_cli core tests tools",
        "pytest",
        TRUST_VERIFICATION_COMMAND,
        "python tools/verify_public_integrity.py",
        "lake build AOSPublicCore",
    ],
}
COMMANDS["full"] = COMMANDS["standard"]
INSTALL_COMMAND = "python -m pip install -e .[dev]"


def resolve(command: str) -> list[str]:
    parts = command.split()
    if not parts:
        raise ValueError("empty command")
    if parts[0] == "python":
        return [sys.executable, *parts[1:]]
    return parts


def verify_trust_verification_output() -> int:
    try:
        payload = load_json_object_path(
            TRUST_VERIFICATION_OUTPUT,
            TRUST_VERIFICATION_LIMITS,
        )
    except OSError as exc:
        print(f"ERROR: trust verification output is missing: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"ERROR: invalid trust verification output: {exc}", file=sys.stderr)
        return 1

    errors = [
        f"{field} must be {expected!r}, observed {payload.get(field)!r}"
        for field, expected in EXPECTED_TRUST_VERIFICATION.items()
        if payload.get(field) != expected
    ]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


def run(command: str) -> int:
    if command.startswith("lake ") and shutil.which("lake") is None:
        print("  [SKIP] lake not available; install Lean to run formal surface build")
        return 0
    result = subprocess.run(resolve(command), cwd=REPO_ROOT, check=False)
    code = int(result.returncode)
    if code != 0:
        return code
    if command == TRUST_VERIFICATION_COMMAND:
        return verify_trust_verification_output()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_const", const="quick", dest="mode")
    mode.add_argument("--standard", action="store_const", const="standard", dest="mode")
    mode.add_argument("--full", action="store_const", const="full", dest="mode")
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args(argv)
    selected = args.mode or "standard"
    commands = list(COMMANDS[selected])
    if not args.skip_install:
        commands.insert(0, INSTALL_COMMAND)
    print(f"validation gate mode: {selected} ({len(commands)} command(s))")
    for index, command in enumerate(commands, start=1):
        print(f"[{index}/{len(commands)}] {command}", flush=True)
        code = run(command)
        if code != 0:
            print(f"ERROR: validation gate stopped at: {command}", file=sys.stderr)
            return code
        print(f"  [PASS] {command}")
    print(f"{selected} validation gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
