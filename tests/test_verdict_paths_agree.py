from __future__ import annotations

import pytest

from core.aos_public_core import (
    DemoIntervalGate,
    derive_signal_verdict,
    derive_verdict,
    parse_signal,
)

LIMIT = 9000
WARN_MARGIN = 1000
SAFE_LIMIT = LIMIT - WARN_MARGIN
BOUNDARY_UPPER_BOUNDS = sorted(
    {
        SAFE_LIMIT - 1,
        SAFE_LIMIT,
        SAFE_LIMIT + 1,
        LIMIT - 1,
        LIMIT,
        LIMIT + 1,
    }
)


@pytest.mark.parametrize("upper_bound", BOUNDARY_UPPER_BOUNDS)
def test_verdict_paths_agree_on_equivalent_boundary_inputs(upper_bound: int) -> None:
    signal = parse_signal(
        {
            "limit": LIMIT,
            "metadata_complete": True,
            "score": upper_bound,
            "signal_id": f"boundary-{upper_bound}",
            "uncertainty": 0,
            "warn_margin": WARN_MARGIN,
        }
    )

    direct_verdict = derive_verdict(
        float(upper_bound),
        float(LIMIT),
        float(WARN_MARGIN),
    )
    interval_verdict = DemoIntervalGate(float(LIMIT), float(WARN_MARGIN)).evaluate(
        float(upper_bound),
        0.0,
    ).verdict
    signal_verdict, _reason = derive_signal_verdict(signal)

    assert direct_verdict == interval_verdict == signal_verdict
