from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Final, cast

from adapters.strict_json import (
    StrictJsonLimits,
    load_json_object_path,
    parse_json_object_bytes,
)

SCHEMA_VERSION: Final = "aos-trusted-output/v0"
PREDICATE_TYPE: Final = "https://rafineria.ai/aos/trusted-output/v1"
ISSUER: Final = "RafineriaAI"
ISSUER_ID: Final = "rafineriaai-aos"
GENERATED_WITH: Final = "AOS Kernel"
PROVIDER: Final = "RafineriaAI"
PACKAGE_NAME: Final = "aos-kernel"
FALLBACK_AOS_VERSION: Final = "0.1.0"
UNSIGNED_NOTICE: Final = (
    "Unsigned output. This is not an official RafineriaAI/AOS signed verdict. "
    "For source-record comparison, verify with --record."
)
OFFICIAL_NOTICE: Final = (
    "Official RafineriaAI/AOS verdict. Signature, evidence integrity, and code "
    "provenance verified."
)
TAMPERED_NOTICE: Final = (
    "Tampered output. AOS/RafineriaAI verdict integrity is damaged."
)
IMPERSONATION_NOTICE: Final = (
    "Issuer claims RafineriaAI/AOS, but trusted verification failed. "
    "Possible impersonation."
)
UNTRUSTED_FORK_NOTICE: Final = (
    "Output produced by an untrusted fork. This is not an official "
    "RafineriaAI/AOS verdict."
)

TRUSTED_OUTPUT_LIMITS: Final = StrictJsonLimits(
    max_bytes=2 * 1024 * 1024,
    max_depth=32,
    max_nodes=120_000,
)
JSONL_RECORD_LIMITS: Final = StrictJsonLimits(
    max_bytes=2 * 1024 * 1024,
    max_depth=32,
    max_nodes=120_000,
)
SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
RECORD_SCHEMA_VERSION: Final = "aos-developer-workflow-record/v1"
VALID_VERDICTS: Final = frozenset({"PASS", "WARN", "BLOCK"})
REQUIRED_RECORD_FIELDS: Final = {
    "schema_version",
    "mode",
    "source_kind",
    "source_ref",
    "source_commit",
    "tool",
    "adapter",
    "adapter_version",
    "input_format",
    "input_sha256",
    "aos_verdict",
    "decision",
    "finding_count",
    "reason",
    "action",
    "status",
    "decision_hash",
}

OFFICIAL_VALID = "OFFICIAL_VALID"
UNSIGNED_NOT_OFFICIAL = "UNSIGNED_NOT_OFFICIAL"
TAMPERED = "TAMPERED"
INVALID_SIGNATURE = "INVALID_SIGNATURE"
UNTRUSTED_ISSUER = "UNTRUSTED_ISSUER"
IMPERSONATION_ATTEMPT = "IMPERSONATION_ATTEMPT"
UNAUTHORIZED_BUILD = "UNAUTHORIZED_BUILD"
UNTRUSTED_FORK = "UNTRUSTED_FORK"
ROLLBACK_DETECTED = "ROLLBACK_DETECTED"
KEY_REVOKED = "KEY_REVOKED"

REQUIRED_OUTPUT_FIELDS: Final = {
    "schema_version",
    "verdict",
    "decision",
    "record_sha256",
    "manifest_sha256",
    "issuer",
    "issuer_id",
    "generated_with",
    "provider",
    "aos_version",
    "source_commit",
    "release_tag",
    "build_hash",
    "policy_hash",
    "signature_status",
    "issuer_trust_status",
    "code_provenance_status",
    "official_aos_output",
    "verdict_trust_notice",
    "claim_boundary",
    "predicate_type",
    "minimum_supported_aos_version",
    "trusted_output_sha256",
}


class TrustedOutputError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _aos_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return FALLBACK_AOS_VERSION


def _version_tuple(value: str) -> tuple[int, int, int]:
    parts = value.split(".")
    normalized = []
    for part in parts[:3]:
        digits = "".join(ch for ch in part if ch.isdigit())
        normalized.append(int(digits or "0"))
    while len(normalized) < 3:
        normalized.append(0)
    return (normalized[0], normalized[1], normalized[2])


def _is_version_older(value: Any, minimum: str) -> bool:
    if not isinstance(value, str) or not value:
        return True
    return _version_tuple(value) < _version_tuple(minimum)


def _manifest_path() -> Path | None:
    env_manifest = os.environ.get("AOS_INTEGRITY_MANIFEST")
    if env_manifest:
        candidate = Path(env_manifest).expanduser()
        if candidate.is_file():
            return candidate.resolve()

    repo_manifest = _repo_root() / "evidence" / "integrity_manifest.json"
    if repo_manifest.is_file():
        return repo_manifest
    return None


def _manifest_sha256_or_missing() -> str:
    manifest = _manifest_path()
    if manifest is None:
        return "missing"
    return file_sha256(manifest)


def _local_manifest_sha256() -> str | None:
    manifest = _manifest_path()
    if manifest is None:
        return None
    return file_sha256(manifest)


def _first_jsonl_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise TrustedOutputError(f"record file not found: {path}")
    data = path.read_bytes()
    if len(data) > JSONL_RECORD_LIMITS.max_bytes:
        raise TrustedOutputError("record JSONL exceeds byte-size limit")
    first_line = b""
    for raw_line in data.splitlines():
        if raw_line.strip():
            first_line = raw_line
            break
    if not first_line:
        raise TrustedOutputError("record JSONL is empty")
    try:
        payload = parse_json_object_bytes(first_line, JSONL_RECORD_LIMITS)
    except ValueError as exc:
        raise TrustedOutputError(f"invalid JSONL record: {exc}") from exc
    return cast(dict[str, Any], payload)


def _claim_boundary() -> dict[str, bool]:
    return {
        "official_signed_verdict_claim": False,
        "cryptographic_signature_claim": False,
        "identity_assurance_claim": False,
        "slsa_compliance_claim": False,
        "tuf_root_claim": False,
        "rekor_transparency_log_claim": False,
        "production_readiness_claim": False,
        "security_audit_claim": False,
        "security_warranty_claim": False,
    }


def _value_as_string(
    record: dict[str, Any],
    *keys: str,
    default: str = "unknown",
) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return default


def _record_hash_material(record: dict[str, Any]) -> dict[str, Any]:
    material = dict(record)
    material.pop("record_sha256", None)
    return material


def _validate_aos_record(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_RECORD_FIELDS.difference(record))
    if missing:
        raise TrustedOutputError("missing AOS record field(s): " + ", ".join(missing))
    if record.get("schema_version") != RECORD_SCHEMA_VERSION:
        raise TrustedOutputError("unsupported AOS record schema_version")
    if record.get("aos_verdict") not in VALID_VERDICTS:
        raise TrustedOutputError("AOS record aos_verdict must be PASS, WARN, or BLOCK")
    for key in (
        "mode",
        "source_kind",
        "source_ref",
        "source_commit",
        "tool",
        "adapter",
        "adapter_version",
        "input_format",
        "decision",
        "reason",
        "action",
        "status",
    ):
        value = record.get(key)
        if not isinstance(value, str) or not value:
            raise TrustedOutputError(f"AOS record {key} must be a non-empty string")
    for key in ("input_sha256", "decision_hash"):
        value = record.get(key)
        if not isinstance(value, str) or not SHA256_RE.match(value):
            raise TrustedOutputError(f"AOS record {key} is malformed")
    finding_count = record.get("finding_count")
    if not isinstance(finding_count, int) or isinstance(finding_count, bool):
        raise TrustedOutputError("AOS record finding_count must be an integer")
    if finding_count < 0:
        raise TrustedOutputError("AOS record finding_count must be non-negative")


def _validated_record_sha256(record: dict[str, Any]) -> str:
    _validate_aos_record(record)
    computed = sha256_hex(_record_hash_material(record))
    claimed = record.get("record_sha256")
    if claimed is None:
        return computed
    if not isinstance(claimed, str) or not SHA256_RE.match(claimed):
        raise TrustedOutputError("record_sha256 is malformed")
    if claimed != computed:
        raise TrustedOutputError("record_sha256 does not match the JSONL record")
    return computed


def _policy_hash(record: dict[str, Any]) -> str:
    value = record.get("decision_hash")
    if isinstance(value, str) and SHA256_RE.match(value):
        return value
    material = {
        "schema_version": record.get("schema_version"),
        "mode": record.get("mode"),
        "tool": record.get("tool"),
        "adapter": record.get("adapter"),
        "adapter_version": record.get("adapter_version"),
        "aos_verdict": record.get("aos_verdict", record.get("verdict")),
        "decision": record.get("decision"),
        "reason": record.get("reason"),
    }
    return sha256_hex(material)


def _trusted_hash_material(output: dict[str, Any]) -> dict[str, Any]:
    material = dict(output)
    material.pop("trusted_output_sha256", None)
    return material


def build_unsigned_trusted_output(record: dict[str, Any]) -> dict[str, Any]:
    _validate_aos_record(record)
    verdict = _value_as_string(record, "aos_verdict", "verdict", "result")
    decision = _value_as_string(record, "decision", "action")
    output: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "predicate_type": PREDICATE_TYPE,
        "verdict": verdict,
        "decision": decision,
        "record_sha256": _validated_record_sha256(record),
        "manifest_sha256": _manifest_sha256_or_missing(),
        "issuer": ISSUER,
        "issuer_id": ISSUER_ID,
        "generated_with": GENERATED_WITH,
        "provider": PROVIDER,
        "aos_version": _aos_version(),
        "minimum_supported_aos_version": _aos_version(),
        "source_commit": _value_as_string(record, "source_commit"),
        "release_tag": None,
        "build_hash": None,
        "policy_hash": _policy_hash(record),
        "signature_status": UNSIGNED_NOT_OFFICIAL,
        "issuer_trust_status": "UNVERIFIED",
        "code_provenance_status": "PUBLIC_DEMONSTRATOR_UNATTESTED",
        "official_aos_output": False,
        "verdict_trust_notice": UNSIGNED_NOTICE,
        "claim_boundary": _claim_boundary(),
    }
    output["trusted_output_sha256"] = sha256_hex(_trusted_hash_material(output))
    return output


def _validate_shape(output: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_OUTPUT_FIELDS.difference(output))
    if missing:
        errors.append("missing required field(s): " + ", ".join(missing))
    if output.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported schema_version")
    if output.get("predicate_type") != PREDICATE_TYPE:
        errors.append("unsupported predicate_type")
    for key in ("record_sha256", "policy_hash", "trusted_output_sha256"):
        value = output.get(key)
        if not isinstance(value, str) or not SHA256_RE.match(value):
            errors.append(f"invalid {key}")
    manifest_sha256 = output.get("manifest_sha256")
    if not (
        isinstance(manifest_sha256, str)
        and (manifest_sha256 == "missing" or SHA256_RE.match(manifest_sha256))
    ):
        errors.append("invalid manifest_sha256")
    for key in ("aos_version", "minimum_supported_aos_version"):
        if not isinstance(output.get(key), str) or not str(output.get(key)):
            errors.append(f"{key} must be a non-empty string")
    if not isinstance(output.get("claim_boundary"), dict):
        errors.append("claim_boundary must be an object")
    if not isinstance(output.get("official_aos_output"), bool):
        errors.append("official_aos_output must be boolean")
    return errors


def _record_matches_output(
    output: dict[str, Any],
    source_record: dict[str, Any] | None,
) -> list[str]:
    if source_record is None:
        return []
    try:
        _validate_aos_record(source_record)
        record_sha256 = _validated_record_sha256(source_record)
    except TrustedOutputError as exc:
        return [str(exc)]

    errors: list[str] = []
    comparisons = {
        "record_sha256": record_sha256,
        "policy_hash": _policy_hash(source_record),
        "verdict": _value_as_string(
            source_record, "aos_verdict", "verdict", "result"
        ),
        "decision": _value_as_string(source_record, "decision", "action"),
        "source_commit": _value_as_string(source_record, "source_commit"),
    }
    for key, expected in comparisons.items():
        if output.get(key) != expected:
            errors.append(f"{key} does not match source record")
    return errors


def verify_trusted_output(
    output: dict[str, Any],
    source_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    shape_errors = _validate_shape(output)
    expected_hash = sha256_hex(_trusted_hash_material(output))
    observed_hash = output.get("trusted_output_sha256")
    record_errors = _record_matches_output(output, source_record)
    local_manifest_sha256 = _local_manifest_sha256()
    output_manifest_sha256 = output.get("manifest_sha256")
    if shape_errors:
        status = INVALID_SIGNATURE
        notice = "; ".join(shape_errors)
    elif observed_hash != expected_hash:
        status = TAMPERED
        notice = TAMPERED_NOTICE
    elif record_errors:
        status = TAMPERED
        notice = "; ".join(record_errors)
    elif (
        local_manifest_sha256 is not None
        and output_manifest_sha256 not in {local_manifest_sha256, "missing"}
    ):
        status = TAMPERED
        notice = "Trusted output manifest hash does not match the local manifest."
    elif output.get("issuer") != ISSUER or output.get("issuer_id") != ISSUER_ID:
        status = UNTRUSTED_FORK
        notice = UNTRUSTED_FORK_NOTICE
    elif output.get("official_aos_output") is True:
        status = IMPERSONATION_ATTEMPT
        notice = IMPERSONATION_NOTICE
    elif output.get("signature_status") == OFFICIAL_VALID:
        status = UNAUTHORIZED_BUILD
        notice = IMPERSONATION_NOTICE
    elif _is_version_older(
        output.get("aos_version"),
        str(output.get("minimum_supported_aos_version")),
    ):
        status = ROLLBACK_DETECTED
        notice = "AOS output was generated by a version below the trusted minimum."
    elif output.get("signature_status") == UNSIGNED_NOT_OFFICIAL:
        status = UNSIGNED_NOT_OFFICIAL
        notice = UNSIGNED_NOTICE
    else:
        status = INVALID_SIGNATURE
        notice = "Unsupported signature_status."

    return {
        "schema_version": "aos-trusted-output-verification/v0",
        "status": status,
        "official_aos_output": status == OFFICIAL_VALID,
        "trusted_output_sha256": (
            observed_hash if isinstance(observed_hash, str) else None
        ),
        "expected_trusted_output_sha256": expected_hash,
        "issuer": output.get("issuer"),
        "issuer_id": output.get("issuer_id"),
        "signature_status": output.get("signature_status"),
        "aos_version": output.get("aos_version"),
        "minimum_supported_aos_version": output.get("minimum_supported_aos_version"),
        "verdict": output.get("verdict"),
        "decision": output.get("decision"),
        "record_sha256": output.get("record_sha256"),
        "source_record_checked": source_record is not None,
        "notice": notice,
    }


def _bool_text(value: Any) -> str:
    return "true" if value is True else "false"


def _print_emit_summary(output: dict[str, Any], output_path: Path) -> None:
    print(f"Trusted Output v0: {output_path}")
    print(f"Status: {output['signature_status']}")
    print(f"Official: {_bool_text(output['official_aos_output'])}")
    print(f"Record: {output['record_sha256']}")
    print(f"Wrapper: {output['trusted_output_sha256']}")
    print("Next: verify with --record to bind the wrapper to the source JSONL.")


def _print_verify_summary(result: dict[str, Any]) -> None:
    status = str(result["status"])
    print("Trusted Output v0: verification completed")
    print(f"Status: {status}")
    print(f"Official: {_bool_text(result.get('official_aos_output'))}")
    print(f"Record checked: {_bool_text(result.get('source_record_checked'))}")
    if result.get("record_sha256") is not None:
        print(f"Record: {result['record_sha256']}")
    if result.get("trusted_output_sha256") is not None:
        print(f"Wrapper: {result['trusted_output_sha256']}")
    if status == OFFICIAL_VALID:
        print("Notice: official signed RafineriaAI/AOS verdict.")
    elif status == UNSIGNED_NOT_OFFICIAL:
        print("Notice: unsigned public demonstrator output; not official.")
    else:
        print(f"Notice: {result.get('notice', 'verification failed')}")


def emit_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit an unsigned Trusted AOS Output wrapper for one JSONL record."
    )
    parser.add_argument("--record", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        record = _first_jsonl_object(args.record)
        output = build_unsigned_trusted_output(record)
    except TrustedOutputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _print_emit_summary(output, args.output)
    return 0


def verify_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a Trusted AOS Output wrapper.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-official", action="store_true")
    args = parser.parse_args(argv)

    try:
        output = dict(load_json_object_path(args.input, TRUSTED_OUTPUT_LIMITS))
        source_record = (
            _first_jsonl_object(args.record) if args.record is not None else None
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except TrustedOutputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = verify_trusted_output(output, source_record=source_record)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    status = str(result["status"])
    _print_verify_summary(result)

    if status not in {OFFICIAL_VALID, UNSIGNED_NOT_OFFICIAL}:
        return 2
    if args.require_official and status != OFFICIAL_VALID:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trusted AOS Output utilities.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    emit = subcommands.add_parser("emit")
    emit.add_argument("--record", required=True, type=Path)
    emit.add_argument("--output", required=True, type=Path)
    verify = subcommands.add_parser("verify")
    verify.add_argument("--input", required=True, type=Path)
    verify.add_argument("--record", type=Path)
    verify.add_argument("--output", type=Path)
    verify.add_argument("--require-official", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "emit":
        forwarded = ["--record", str(args.record), "--output", str(args.output)]
        return emit_main(forwarded)
    if args.command == "verify":
        forwarded = ["--input", str(args.input)]
        if args.record is not None:
            forwarded.extend(["--record", str(args.record)])
        if args.output is not None:
            forwarded.extend(["--output", str(args.output)])
        if args.require_official:
            forwarded.append("--require-official")
        return verify_main(forwarded)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
