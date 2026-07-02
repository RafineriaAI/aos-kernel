from __future__ import annotations

import hashlib
import json
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


def verify() -> list[str]:
    payload = load_manifest()
    if payload.get("schema_version") != "aos-kernel-integrity-manifest/v1":
        return ["unsupported integrity manifest schema_version"]
    files = payload.get("files")
    if not isinstance(files, list):
        return ["integrity manifest files must be a list"]
    errors: list[str] = []
    seen: set[str] = set()
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