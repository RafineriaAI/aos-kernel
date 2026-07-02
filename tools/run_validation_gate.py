from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

COMMANDS = {
    "quick": [
        "python tools/verify_public_integrity.py",
        "pytest",
    ],
    "standard": [
        "ruff check .",
        "mypy adapters aos_cli core tests tools",
        "pytest",
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


def run(command: str) -> int:
    if command.startswith("lake ") and shutil.which("lake") is None:
        print("  [SKIP] lake not available; install Lean to run formal surface build")
        return 0
    result = subprocess.run(resolve(command), cwd=REPO_ROOT, check=False)
    return int(result.returncode)


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