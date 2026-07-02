from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, replace
from typing import Any

import pytest

from core.aos_public_core import (
    REFERENCE_IMPLEMENTATION_ONLY,
    DemoIntervalGate,
    build_signal_evidence,
    derive_verdict,
    parse_signal,
    verify_signal_evidence,
)


def _canonical_signal_evidence_packet() -> dict[str, Any]:
    signal = parse_signal(
        {
            "limit": 9000,
            "metadata_complete": True,
            "score": 8200,
            "signal_id": "demo-signal-001",
            "uncertainty": 1200,
            "warn_margin": 1000,
        }
    )
    return asdict(build_signal_evidence(signal))


def _evidence_packet_is_rejected(packet: dict[str, Any]) -> bool:
    try:
        return verify_signal_evidence(packet)["valid"] is False
    except (KeyError, TypeError, ValueError):
        return True


def test_reference_flag_is_explicit() -> None:
    assert REFERENCE_IMPLEMENTATION_ONLY is True


def test_pass_warn_block_boundaries() -> None:
    gate = DemoIntervalGate(limit=100.0, warn_margin=5.0)

    assert gate.evaluate(95.0, 0.0).verdict == "PASS"
    assert gate.evaluate(95.0, 0.1).verdict == "WARN"
    assert gate.evaluate(99.0, 1.0).verdict == "WARN"
    assert gate.evaluate(99.0, 1.1).verdict == "BLOCK"


def test_decimal_interval_boundaries_for_non_integer_inputs() -> None:
    gate = DemoIntervalGate(limit=0.3, warn_margin=0.1)

    assert gate.evaluate(0.1, 0.1).verdict == "PASS"
    assert gate.evaluate(0.1, 0.2).verdict == "WARN"
    assert gate.evaluate(0.1, 0.20000000000000004).verdict == "BLOCK"


def test_demo_audit_digest_detects_tampering() -> None:
    record = DemoIntervalGate(100.0, 5.0).evaluate(90.0, 2.0)

    assert record.verify_demo_digest()
    assert not replace(record, value=91.0).verify_demo_digest()


def test_demo_record_is_immutable() -> None:
    record = DemoIntervalGate(100.0, 5.0).evaluate(90.0, 2.0)

    with pytest.raises(FrozenInstanceError):
        record.value = 1.0  # type: ignore


@pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf])
def test_non_finite_inputs_are_rejected(bad_value: float) -> None:
    gate = DemoIntervalGate(100.0, 5.0)

    with pytest.raises(ValueError):
        gate.evaluate(bad_value, 0.0)

    with pytest.raises(ValueError):
        gate.evaluate(1.0, bad_value)


def test_negative_uncertainty_and_warn_margin_are_rejected() -> None:
    with pytest.raises(ValueError):
        DemoIntervalGate(100.0, -1.0)

    with pytest.raises(ValueError):
        DemoIntervalGate(100.0, 5.0).evaluate(90.0, -1.0)


def test_upper_bound_overflow_is_rejected() -> None:
    with pytest.raises(ValueError):
        DemoIntervalGate(1e308, 5.0).evaluate(1e308, 1e308)


def test_abstract_verdict_function() -> None:
    assert derive_verdict(90.0, 100.0, 5.0) == "PASS"
    assert derive_verdict(96.0, 100.0, 5.0) == "WARN"
    assert derive_verdict(101.0, 100.0, 5.0) == "BLOCK"


@pytest.mark.parametrize(
    ("score", "uncertainty", "expected_verdict"),
    (
        (7000, 1000, "PASS"),
        (8000, 1000, "WARN"),
        (8001, 1000, "BLOCK"),
    ),
)
def test_signal_interval_order_boundaries(
    score: int,
    uncertainty: int,
    expected_verdict: str,
) -> None:
    signal = parse_signal(
        {
            "limit": 9000,
            "metadata_complete": True,
            "score": score,
            "signal_id": "boundary-signal",
            "uncertainty": uncertainty,
            "warn_margin": 1000,
        }
    )

    assert build_signal_evidence(signal).verdict == expected_verdict


def test_canonical_signal_evidence_replays() -> None:
    evidence_packet = _canonical_signal_evidence_packet()
    result = verify_signal_evidence(evidence_packet)

    assert evidence_packet["verdict"] == "BLOCK"
    assert str(evidence_packet["audit_id"]).startswith("sha256:")
    assert result["valid"] is True
    assert result["mismatches"] == []


def test_demo_signal_evidence_contract_is_unchanged() -> None:
    assert _canonical_signal_evidence_packet() == {
        "audit_id": (
            "sha256:e545f9db7dac16f41dd2aef400efb377e47d4d8afee34a6736a408b1254bca7e"
        ),
        "claim_boundary": {
            "external_validation_claim": False,
            "production_use_claim": False,
            "regulated_use_claim": False,
        },
        "input": {
            "limit": 9000,
            "metadata_complete": True,
            "policy_id": "demo_gate_policy_v1",
            "policy_version": "1.0.0",
            "score": 8200,
            "signal_id": "demo-signal-001",
            "uncertainty": 1200,
            "warn_margin": 1000,
        },
        "input_digest": (
            "sha256:fc96f9b6deb3d6c25efed961dcff5888fb0b20f68e89e3cbab4a5edc47ccb8fc"
        ),
        "policy_id": "demo_gate_policy_v1",
        "policy_version": "1.0.0",
        "reason": "Score plus uncertainty exceeds the allowed envelope.",
        "replayable": True,
        "schema_version": "aos-demo-evidence/v1",
        "signal_id": "demo-signal-001",
        "verdict": "BLOCK",
    }


def test_integrity_verification_rejects_tampered_score() -> None:
    packet = deepcopy(_canonical_signal_evidence_packet())
    packet["input"]["score"] = 7000

    assert _evidence_packet_is_rejected(packet)


def test_integrity_verification_rejects_tampered_verdict() -> None:
    packet = deepcopy(_canonical_signal_evidence_packet())
    packet["verdict"] = "PASS"

    assert _evidence_packet_is_rejected(packet)


def test_integrity_verification_rejects_corrupted_evidence_payload() -> None:
    packet = deepcopy(_canonical_signal_evidence_packet())
    packet["input"]["uncertainty"] = -1

    assert _evidence_packet_is_rejected(packet)


@pytest.mark.parametrize("field", ("audit_id", "input_digest"))
def test_integrity_verification_rejects_missing_evidence_fields(field: str) -> None:
    packet = deepcopy(_canonical_signal_evidence_packet())
    packet.pop(field)

    assert _evidence_packet_is_rejected(packet)


@pytest.mark.parametrize("field", ("audit_id", "input_digest"))
def test_integrity_verification_rejects_empty_evidence_fields(field: str) -> None:
    packet = deepcopy(_canonical_signal_evidence_packet())
    packet[field] = ""

    assert _evidence_packet_is_rejected(packet)


def test_integrity_verification_rejects_malformed_evidence_structure() -> None:
    packet = deepcopy(_canonical_signal_evidence_packet())
    packet["input"] = ["not", "an", "object"]

    assert _evidence_packet_is_rejected(packet)


def test_incomplete_signal_blocks_before_numeric_band() -> None:
    signal = parse_signal(
        {
            "limit": 9000,
            "metadata_complete": False,
            "score": 100,
            "signal_id": "incomplete-signal",
            "uncertainty": 0,
            "warn_margin": 1000,
        }
    )
    evidence = build_signal_evidence(signal)

    assert evidence.verdict == "BLOCK"
    assert evidence.reason == "Required metadata is incomplete."


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("score", -1),
        ("uncertainty", -1),
        ("limit", -1),
        ("warn_margin", -1),
    ),
)
def test_signal_parser_rejects_negative_contract_inputs(
    field: str,
    value: int,
) -> None:
    payload: dict[str, Any] = {
        "limit": 9000,
        "metadata_complete": True,
        "score": 7000,
        "signal_id": "invalid-signal",
        "uncertainty": 1000,
        "warn_margin": 1000,
    }
    payload[field] = value

    with pytest.raises(ValueError):
        parse_signal(payload)


@pytest.mark.parametrize(
    ("limit", "warn_margin"),
    (
        (0, 0),
        (1000, 1000),
        (1000, 1001),
    ),
)
def test_signal_parser_rejects_invalid_policy_band(
    limit: int,
    warn_margin: int,
) -> None:
    with pytest.raises(ValueError):
        parse_signal(
            {
                "limit": limit,
                "metadata_complete": True,
                "score": 0,
                "signal_id": "invalid-policy",
                "uncertainty": 0,
                "warn_margin": warn_margin,
            }
        )
