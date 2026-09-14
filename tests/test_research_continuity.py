from datetime import datetime, timezone

from research_core.data_quality_treatment import ContinuityBreak
from research_core.research_continuity import AlternativeSourceCandidate, DATA_BOUNDARY_TERMINATION, segment_series, trade_boundary_termination

UTC = timezone.utc


def test_equity_or_benchmark_series_segments_at_break_without_fill():
    timestamps = [datetime(2024, 1, 1, hour=h, tzinfo=UTC) for h in range(4)]
    values = [100, 101, 102, 103]
    br = ContinuityBreak(timestamps[2].isoformat(), timestamps[3].isoformat(), ("x",), "break")
    segments = segment_series(timestamps, values, (br,))
    assert segments == (((timestamps[0], 100), (timestamps[1], 101)), ((timestamps[3], 103),))


def test_trade_boundary_termination_is_not_a_strategy_exit():
    timestamp = datetime(2024, 1, 1, 2, tzinfo=UTC)
    br = ContinuityBreak(timestamp.isoformat(), datetime(2024, 1, 1, 3, tzinfo=UTC).isoformat(), ("x",), "break")
    assert trade_boundary_termination(timestamp, (br,)) == DATA_BOUNDARY_TERMINATION


def test_alternative_source_never_auto_replaces_binance_data():
    candidate = AlternativeSourceCandidate("alt", True, True, True, True, True, True, True)
    assert candidate.approval_status == "REQUIRES SEPARATE APPROVAL"
    assert candidate.eligible_for_replacement is False
