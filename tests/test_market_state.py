from datetime import datetime, timedelta, timezone
from decimal import Decimal

from research_core.data_interfaces import MarketBar
from research_core.market_state import (
    PERCENTILE_REFERENCE_COUNT,
    STATE_DEFINITION_VERSION,
    _rolling_percentile_ranks,
    build_market_states,
)


def bar(i: int, close: Decimal | str = "100", volume: Decimal | str = "1") -> MarketBar:
    close = Decimal(close)
    volume = Decimal(volume)
    return MarketBar(
        timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i),
        symbol="BTC/USDT",
        open=close,
        high=close,
        low=close,
        close=close,
        volume=volume,
    )


def test_ams_v1_version_and_reference_count_are_frozen():
    assert STATE_DEFINITION_VERSION == "AMS-V1"
    assert PERCENTILE_REFERENCE_COUNT == 720


def test_percentile_rank_requires_exactly_720_prior_observations():
    values = [Decimal(i + 1) for i in range(720)]
    assert all(x is None for x in _rolling_percentile_ranks(values))

    values.append(Decimal("360"))
    ranks = _rolling_percentile_ranks(values)
    assert ranks[720] is not None


def test_current_observation_is_excluded_from_reference_distribution():
    values = [Decimal("100")] * 720 + [Decimal("0")]
    ranks = _rolling_percentile_ranks(values)
    assert ranks[720] == Decimal("0")


def test_percentile_boundaries_implement_low_20_and_high_80_exactly():
    refs = [Decimal(i) for i in range(1, 721)]

    low_rank = _rolling_percentile_ranks(refs + [Decimal("144")])[720]
    high_rank = _rolling_percentile_ranks(refs + [Decimal("576")])[720]

    assert low_rank == Decimal("0.20")
    assert high_rank == Decimal("0.80")

    # Use a long synthetic sequence only to exercise label assignment.
    bars = [bar(i, close=Decimal("100") + Decimal(i) / Decimal("100"), volume=Decimal(i + 1)) for i in range(900)]
    states = build_market_states(bars)
    assert any(s.volatility_state is not None for s in states)
    assert any(s.activity_state is not None for s in states)


def test_trend_thresholds_are_strict():
    neutral = [bar(i, close="100") for i in range(169)]
    neutral[-1] = bar(168, close="110")
    assert build_market_states(neutral)[168].trend_state == "TREND_NEUTRAL"

    bull = [bar(i, close="100") for i in range(169)]
    bull[-1] = bar(168, close="110.01")
    assert build_market_states(bull)[168].trend_state == "TREND_BULL"

    bear = [bar(i, close="100") for i in range(169)]
    bear[-1] = bar(168, close="89.99")
    assert build_market_states(bear)[168].trend_state == "TREND_BEAR"


def test_complete_state_requires_all_three_axes():
    bars = [bar(i, close=Decimal("100") + Decimal(i) / Decimal("100"), volume=Decimal(i + 1)) for i in range(744)]
    states = build_market_states(bars)
    assert states[-1].volatility_state is None
    assert states[-1].activity_state is not None
    assert states[-1].trend_state is not None
    assert states[-1].complete is False
    assert states[-1].composite is None

    bars.append(bar(744, close="108", volume="900"))
    state = build_market_states(bars)[744]
    assert state.volatility_state is not None
    assert state.activity_state is not None
    assert state.trend_state is not None
    assert state.complete is True
    assert state.composite is not None


def test_future_bar_mutation_does_not_change_past_state():
    bars = []
    for i in range(800):
        close = Decimal("100") + Decimal(i) / Decimal("100")
        volume = Decimal((i % 50) + 1)
        bars.append(bar(i, close=close, volume=volume))

    before = build_market_states(bars)[760]

    bars[799] = MarketBar(
        timestamp=bars[799].timestamp,
        symbol="BTC/USDT",
        open=Decimal("1000"),
        high=Decimal("2000"),
        low=Decimal("1"),
        close=Decimal("1500"),
        volume=Decimal("999999"),
    )
    after = build_market_states(bars)[760]
    assert before == after


def test_warmup_resets_across_continuity_segments():
    first = [bar(i, close=Decimal("100") + Decimal(i) / Decimal("100"), volume="10") for i in range(500)]
    second = [
        MarketBar(
            timestamp=datetime(2021, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i),
            symbol="BTC/USDT",
            open=Decimal("100"),
            high=Decimal("100"),
            low=Decimal("100"),
            close=Decimal("100"),
            volume=Decimal("10"),
        )
        for i in range(500)
    ]

    assert not any(s.complete for s in build_market_states(first))
    assert not any(s.complete for s in build_market_states(second))
