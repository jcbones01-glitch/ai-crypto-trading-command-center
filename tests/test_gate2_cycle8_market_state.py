from datetime import datetime, timedelta, timezone

from research_core.market_state import MarketState
from tests.gate2_cycle8_market_state_experiments import synchronized_agreement


def state(hour, vol, activity, trend):
    return MarketState(
        timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc) + timedelta(hours=hour),
        volatility_state=vol,
        activity_state=activity,
        trend_state=trend,
    )


def test_synchronized_agreement_uses_only_exact_complete_timestamps():
    btc = [[
        state(0, "VOL_LOW", "ACTIVITY_LOW", "TREND_NEUTRAL"),
        state(1, "VOL_HIGH", "ACTIVITY_HIGH", "TREND_BULL"),
        state(2, None, "ACTIVITY_HIGH", "TREND_BULL"),
    ]]
    eth = [[
        state(0, "VOL_LOW", "ACTIVITY_NORMAL", "TREND_NEUTRAL"),
        state(1, "VOL_NORMAL", "ACTIVITY_HIGH", "TREND_BULL"),
        state(3, "VOL_HIGH", "ACTIVITY_HIGH", "TREND_BEAR"),
    ]]

    result = synchronized_agreement(btc, eth)

    assert result["synchronized_complete_state_observations"] == 2
    assert result["volatility_state_agreement_fraction"] == "0.5"
    assert result["activity_state_agreement_fraction"] == "0.5"
    assert result["trend_state_agreement_fraction"] == "1"
    assert result["composite_state_agreement_fraction"] == "0.5"
