from decimal import Decimal

from tests.gate2_next_cycle_experiments import concentration_and_dd


def test_concentration_and_dd_consumes_event_record_dicts():
    details = [
        {
            "segment": 0,
            "aggregate": {
                "events": 2,
                "compound_return": "0.0099",
            },
            "events": [
                {"return": "0.01", "signal_index": 1},
                {"return": "-0.000099", "signal_index": 2},
            ],
            "error": None,
        }
    ]

    result = concentration_and_dd(details)

    assert result["eligible_events"] == 2
    assert Decimal(result["max_drawdown"]) >= Decimal("0")
    assert Decimal(result["worst_segment_return"]) == Decimal("0.0099")
    assert int(result["longest_recovery_events"]) >= 0
    assert Decimal(result["top_10_positive_event_pnl_fraction"]) == Decimal("1")
