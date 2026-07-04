from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Final, Sequence, cast

from adapters.strict_json import StrictJsonLimits, load_json_object_path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "evidence" / "integrity_manifest.json"
MANIFEST_LIMITS: Final = StrictJsonLimits(
    max_bytes=2 * 1024 * 1024,
    max_depth=32,
    max_nodes=120_000,
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict[str, object]:
    return cast(dict[str, object], load_json_object_path(MANIFEST, MANIFEST_LIMITS))


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


def _validated_manifest_metadata(
    payload: dict[str, object],
) -> tuple[str, str, list[str]]:
    schema_version = payload.get("schema_version")
    if schema_version != "aos-kernel-integrity-manifest/v1":
        raise ValueError("unsupported integrity manifest schema_version")
    repository_role = payload.get("repository_role")
    if not isinstance(repository_role, str) or not repository_role:
        raise ValueError("integrity manifest repository_role must be a string")
    excludes_value = payload.get("excludes")
    if not isinstance(excludes_value, list) or not all(
        isinstance(path, str) and path for path in excludes_value
    ):
        raise ValueError("integrity manifest excludes must be a list of paths")
    return schema_version, repository_role, cast(list[str], excludes_value)


def update_manifest() -> None:
    payload = load_manifest()
    schema_version, repository_role, excludes = _validated_manifest_metadata(payload)
    tracked_paths = git_tracked_paths()
    if tracked_paths is None:
        raise RuntimeError("git ls-files is required to update integrity manifest")
    excluded_paths = set(excludes)
    files: list[dict[str, str]] = []
    for path_value in tracked_paths:
        if path_value in excluded_paths:
            continue
        path = (REPO_ROOT / path_value).resolve()
        if REPO_ROOT.resolve() not in (path, *path.parents):
            raise RuntimeError(f"manifest path escapes repository: {path_value}")
        if not path.is_file():
            raise RuntimeError(f"tracked manifest path is missing: {path_value}")
        files.append({"path": path_value, "sha256": file_sha256(path)})
    updated = {
        "schema_version": schema_version,
        "repository_role": repository_role,
        "excludes": excludes,
        "files": files,
    }
    with MANIFEST.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(updated, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update",
        action="store_true",
        help="rewrite the integrity manifest from git-tracked files before verifying",
    )
    args = parser.parse_args(argv)
    if args.update:
        try:
            update_manifest()
        except (RuntimeError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print("public integrity manifest updated")
    errors = verify()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("public integrity check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())