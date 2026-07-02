from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "evidence" / "integrity_manifest.json"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict[str, object]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("integrity manifest must be a JSON object")
    return payload


def git_tracked_paths() -> list[str] | None:
    if not (REPO_ROOT / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line]


def verify() -> list[str]:
    payload = load_manifest()
    if payload.get("schema_version") != "aos-kernel-integrity-manifest/v1":
        return ["unsupported integrity manifest schema_version"]
    files = payload.get("files")
    if not isinstance(files, list):
        return ["integrity manifest files must be a list"]
    excludes = payload.get("excludes")
    if not isinstance(excludes, list) or not all(
        isinstance(path, str) and path for path in excludes
    ):
        return ["integrity manifest excludes must be a list of paths"]
    errors: list[str] = []
    seen: set[str] = set()
    excluded_paths = set(excludes)
    for item in files:
        if not isinstance(item, dict):
            errors.append("integrity manifest entry must be an object")
            continue
        path_value = item.get("path")
        expected = item.get("sha256")
        if not isinstance(path_value, str) or not path_value:
            errors.append("integrity manifest entry has invalid path")
            continue
        if path_value in seen:
            errors.append(f"duplicate manifest path: {path_value}")
        seen.add(path_value)
        if not isinstance(expected, str) or len(expected) != 64:
            errors.append(f"invalid expected hash for {path_value}")
            continue
        path = (REPO_ROOT / path_value).resolve()
        if REPO_ROOT.resolve() not in (path, *path.parents):
            errors.append(f"manifest path escapes repository: {path_value}")
            continue
        if not path.is_file():
            errors.append(f"manifest path is missing: {path_value}")
            continue
        observed = file_sha256(path)
        if observed != expected:
            errors.append(
                f"hash mismatch for {path_value}: expected {expected}, "
                f"observed {observed}"
            )
    tracked_paths = git_tracked_paths()
    if tracked_paths is not None:
        listed_paths = seen
        expected_paths = set(tracked_paths).difference(excluded_paths)
        for missing_path in sorted(expected_paths.difference(listed_paths)):
            errors.append(f"manifest is missing tracked path: {missing_path}")
        for extra_path in sorted(listed_paths.difference(expected_paths)):
            errors.append(f"manifest lists untracked path: {extra_path}")
    return errors


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("public integrity check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())