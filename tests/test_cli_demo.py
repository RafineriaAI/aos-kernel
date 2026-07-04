from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import asdict
from pathlib import Path

import pytest

from aos_cli import cli
from core.aos_public_core import build_signal_evidence, parse_signal


def _test_dir(name: str) -> Path:
    path = Path("tests/.tmp_cli_demo") / f"{name}-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    return path


def _line_value(output: str, prefix: str) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    raise AssertionError(f"missing output line: {prefix}")


def test_cli_demo_prints_values_from_computed_evidence(
    capsys: pytest.CaptureFixture[str],
) -> None:
    work_dir = _test_dir("computed_evidence")
    try:
        assert cli.main(["demo", "--output-dir", str(work_dir)]) == 0
        output = capsys.readouterr().out

        record_path = work_dir / "check-record.jsonl"
        summary_path = work_dir / "check-summary.md"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        evidence = record["kernel_evidence"]
        computed = asdict(build_signal_evidence(parse_signal(evidence["input"])))

        assert summary_path.is_file()
        assert evidence == computed
        assert record["aos_verdict"] == computed["verdict"]
        assert _line_value(output, "Verdict:") == computed["verdict"]
        assert _line_value(output, "Decision:") == record["decision"]
        assert _line_value(output, "Signals:") == str(record["finding_count"])
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def test_cli_verdict_rejects_duplicate_json_keys(
    capsys: pytest.CaptureFixture[str],
) -> None:
    work_dir = _test_dir("duplicate_keys")
    try:
        input_path = work_dir / "signal.json"
        input_path.write_text(
            "{"
            '"signal_id":"one",'
            '"signal_id":"two",'
            '"score":1,'
            '"uncertainty":0,'
            '"limit":10,'
            '"warn_margin":1,'
            '"metadata_complete":true'
            "}",
            encoding="utf-8",
        )

        assert cli.main(["verdict", "--input", str(input_path)]) == 1
        assert "duplicate JSON object key" in capsys.readouterr().err
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
