from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from aos_cli import cli
from aos_cli import trusted_output as trusted_module
from aos_cli.trusted_output import (
    IMPERSONATION_ATTEMPT,
    ROLLBACK_DETECTED,
    TAMPERED,
    UNAUTHORIZED_BUILD,
    UNSIGNED_NOT_OFFICIAL,
    UNTRUSTED_FORK,
    TrustedOutputError,
    build_unsigned_trusted_output,
    sha256_hex,
    verify_trusted_output,
)


def _record_without_hash() -> dict[str, object]:
    return {
        "schema_version": "aos-developer-workflow-record/v1",
        "mode": "gate",
        "source_kind": "sarif",
        "source_ref": "https://github.com/example/repo",
        "source_commit": "0123456789abcdef0123456789abcdef01234567",
        "base_commit": "unknown",
        "tool": "semgrep",
        "adapter": "aos_sarif_import",
        "adapter_version": "aos-sarif-result-import/v1",
        "input_format": "sarif-2.1.0",
        "input_sha256": "a" * 64,
        "aos_verdict": "WARN",
        "decision": "REVIEW_REQUIRED",
        "finding_count": 3,
        "reason": "3_reviewable_signal(s)_present",
        "action": "review_required_before_merge",
        "status": "ok",
        "decision_hash": "b" * 64,
    }


def _record() -> dict[str, object]:
    record = _record_without_hash()
    record["record_sha256"] = sha256_hex(record)
    return record


def _rehash(output: dict[str, object]) -> dict[str, object]:
    output = dict(output)
    output.pop("trusted_output_sha256", None)
    output["trusted_output_sha256"] = sha256_hex(output)
    return output


def _test_dir(name: str) -> Path:
    path = Path("tests/.tmp_trusted_output") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def _emit_wrapper(work_dir: Path) -> Path:
    record_path = work_dir / "record.jsonl"
    wrapper_path = work_dir / "wrapper.json"
    record_path.write_text(
        json.dumps(_record(), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert (
        cli.main(
            [
                "trust",
                "emit",
                "--record",
                str(record_path),
                "--output",
                str(wrapper_path),
            ]
        )
        == 0
    )
    return wrapper_path


def test_unsigned_trusted_output_is_integrity_checked_not_official() -> None:
    wrapper = build_unsigned_trusted_output(_record())

    assert wrapper["issuer"] == "RafineriaAI"
    assert wrapper["issuer_id"] == "rafineriaai-aos"
    assert wrapper["official_aos_output"] is False
    assert wrapper["signature_status"] == UNSIGNED_NOT_OFFICIAL
    assert wrapper["minimum_supported_aos_version"] == wrapper["aos_version"]

    result = verify_trusted_output(wrapper)
    assert result["status"] == UNSIGNED_NOT_OFFICIAL
    assert result["official_aos_output"] is False


def test_trusted_output_detects_tampering() -> None:
    wrapper = build_unsigned_trusted_output(_record())
    wrapper["decision"] = "MERGE_OK"

    result = verify_trusted_output(wrapper)
    assert result["status"] == TAMPERED


def test_trusted_output_rejects_mismatched_record_hash() -> None:
    record = _record()
    record["finding_count"] = 4

    try:
        build_unsigned_trusted_output(record)
    except TrustedOutputError as exc:
        assert "record_sha256 does not match" in str(exc)
    else:
        raise AssertionError("mismatched record_sha256 was accepted")


def test_trusted_output_detects_manifest_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(trusted_module, "_manifest_sha256_or_missing", lambda: "c" * 64)
    monkeypatch.setattr(trusted_module, "_local_manifest_sha256", lambda: "c" * 64)

    wrapper = build_unsigned_trusted_output(_record())
    wrapper["manifest_sha256"] = "d" * 64
    wrapper = _rehash(wrapper)

    result = verify_trusted_output(wrapper)
    assert result["status"] == TAMPERED


def test_trusted_output_detects_untrusted_fork() -> None:
    wrapper = build_unsigned_trusted_output(_record())
    wrapper["issuer"] = "ForkedVendor"
    wrapper["issuer_id"] = "forked-aos"
    wrapper = _rehash(wrapper)

    result = verify_trusted_output(wrapper)
    assert result["status"] == UNTRUSTED_FORK


def test_trusted_output_detects_impersonation_attempt() -> None:
    wrapper = build_unsigned_trusted_output(_record())
    wrapper["official_aos_output"] = True
    wrapper["signature_status"] = "OFFICIAL_VALID"
    wrapper = _rehash(wrapper)

    result = verify_trusted_output(wrapper)
    assert result["status"] == IMPERSONATION_ATTEMPT


def test_trusted_output_detects_unauthorized_official_signature_status() -> None:
    wrapper = build_unsigned_trusted_output(_record())
    wrapper["signature_status"] = "OFFICIAL_VALID"
    wrapper = _rehash(wrapper)

    result = verify_trusted_output(wrapper)
    assert result["status"] == UNAUTHORIZED_BUILD


def test_trusted_output_detects_older_aos_version() -> None:
    wrapper = build_unsigned_trusted_output(_record())
    wrapper["aos_version"] = "0.0.1"
    wrapper["minimum_supported_aos_version"] = "0.1.0"
    wrapper = _rehash(wrapper)

    result = verify_trusted_output(wrapper)
    assert result["status"] == ROLLBACK_DETECTED


def test_trusted_output_rejects_non_aos_record() -> None:
    with pytest.raises(TrustedOutputError, match="missing AOS record field"):
        build_unsigned_trusted_output({})


def test_cli_trust_emit_rejects_duplicate_json_keys() -> None:
    work_dir = _test_dir("duplicate_keys")
    try:
        record_path = work_dir / "record.jsonl"
        wrapper_path = work_dir / "wrapper.json"
        record_path.write_text(
            '{"schema_version":"aos-developer-workflow-record/v1",'
            '"schema_version":"aos-developer-workflow-record/v1"}\n',
            encoding="utf-8",
        )

        assert (
            cli.main(
                [
                    "trust",
                    "emit",
                    "--record",
                    str(record_path),
                    "--output",
                    str(wrapper_path),
                ]
            )
            == 2
        )
        assert not wrapper_path.exists()
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def test_trusted_output_verify_with_source_record_detects_self_rehash() -> None:
    record = _record()
    wrapper = build_unsigned_trusted_output(record)
    wrapper["decision"] = "MERGE_OK"
    wrapper = _rehash(wrapper)

    without_record = verify_trusted_output(wrapper)
    with_record = verify_trusted_output(wrapper, source_record=record)

    assert without_record["status"] == UNSIGNED_NOT_OFFICIAL
    assert without_record["source_record_checked"] is False
    assert with_record["status"] == TAMPERED
    assert with_record["source_record_checked"] is True


def test_cli_trust_verify_with_record_detects_record_mismatch() -> None:
    work_dir = _test_dir("verify_record_mismatch")
    try:
        record = _record()
        record_path = work_dir / "record.jsonl"
        wrapper_path = Path("examples/reports/public-replay-trusted-output.json")
        record_path.write_text(
            json.dumps(record, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        assert (
            cli.main(
                [
                    "trust",
                    "verify",
                    "--input",
                    str(wrapper_path),
                    "--record",
                    str(record_path),
                ]
            )
            == 2
        )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def test_trusted_output_can_emit_when_manifest_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(trusted_module, "_manifest_path", lambda: None)

    wrapper = build_unsigned_trusted_output(_record())
    result = verify_trusted_output(wrapper)

    assert wrapper["manifest_sha256"] == "missing"
    assert result["status"] == UNSIGNED_NOT_OFFICIAL


def test_cli_trust_emit_and_verify(capsys: pytest.CaptureFixture[str]) -> None:
    work_dir = _test_dir("emit_verify")
    try:
        wrapper_path = _emit_wrapper(work_dir)
        emit_output = capsys.readouterr().out
        verification_path = work_dir / "verification.json"
        assert wrapper_path.is_file()
        assert "Trusted Output v0:" in emit_output
        assert "Status: UNSIGNED_NOT_OFFICIAL" in emit_output
        assert "Official: false" in emit_output
        assert "Wrapper:" in emit_output

        assert (
            cli.main(
                [
                    "trust",
                    "verify",
                    "--input",
                    str(wrapper_path),
                    "--output",
                    str(verification_path),
                ]
            )
            == 0
        )
        verify_output = capsys.readouterr().out
        verification = json.loads(verification_path.read_text(encoding="utf-8"))
        assert verification["status"] == UNSIGNED_NOT_OFFICIAL
        assert "Trusted Output v0: verification completed" in verify_output
        assert "Record checked: false" in verify_output
        assert "Notice: unsigned public demonstrator output" in verify_output
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def test_cli_trust_verify_requires_official_when_requested() -> None:
    work_dir = _test_dir("require_official")
    try:
        wrapper_path = _emit_wrapper(work_dir)
        assert (
            cli.main(
                [
                    "trust",
                    "verify",
                    "--input",
                    str(wrapper_path),
                    "--require-official",
                ]
            )
            == 1
        )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def test_trust_verify_main_rejects_failure_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        trusted_module,
        "load_json_object_path",
        lambda _path, _limits: {"schema_version": "test-wrapper"},
    )
    monkeypatch.setattr(
        trusted_module,
        "verify_trusted_output",
        lambda _output, source_record=None: {"status": TAMPERED},
    )

    assert trusted_module.verify_main(["--input", "ignored.json"]) == 2
