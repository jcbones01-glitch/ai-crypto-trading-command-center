"""Synthetic/offline tests for PSR-01B revision-4 numerical primitives."""
from datetime import datetime, timezone
import hashlib
import struct

import numpy as np
import pytest

import research_core.psr01b_core as coremod
from research_core.psr01b_core import (
    BOOTSTRAP_ROOT,
    FORECAST_PREFIX,
    PSR01BError,
    classify_success,
    evaluate_strategy_segments,
    forecast_vector_sha256,
    holm_two,
    paired_segment_bootstrap,
    performance_metrics,
    seed_from_coordinates,
    split_origin_eligible,
)


UTC = timezone.utc


def test_seed_engine_matches_registered_seedsequence_rule():
    coords = (2026092401, 1, 0, 3)
    expected = int(np.random.SeedSequence(list(coords)).generate_state(1, dtype=np.uint32)[0])
    assert seed_from_coordinates(*coords) == expected
    assert seed_from_coordinates(*coords) == seed_from_coordinates(*coords)
    assert seed_from_coordinates(2026092401, 1, 0, 4) != expected


def test_split_endpoint_rule_is_half_open_and_target_must_stay_inside():
    start = datetime(2021, 10, 1, tzinfo=UTC)
    end = datetime(2022, 1, 1, tzinfo=UTC)
    assert split_origin_eligible(datetime(2021, 12, 31, 22, tzinfo=UTC), start, end)
    assert not split_origin_eligible(datetime(2021, 12, 31, 23, tzinfo=UTC), start, end)
    assert not split_origin_eligible(datetime(2021, 9, 30, 23, tzinfo=UTC), start, end)


def test_forecast_hash_exact_binary_contract():
    stamps = [1_700_000_000, 1_700_003_600]
    forecasts = [0.125, -0.5]
    payload = bytearray(FORECAST_PREFIX)
    payload.extend(struct.pack("<Q", 2))
    payload.extend(struct.pack("<qd", stamps[0], forecasts[0]))
    payload.extend(struct.pack("<qd", stamps[1], forecasts[1]))
    expected = hashlib.sha256(bytes(payload)).hexdigest()
    assert forecast_vector_sha256(stamps, forecasts) == expected


@pytest.mark.parametrize(
    "stamps,forecasts",
    [
        ([2, 1], [0.1, 0.2]),
        ([1, 1], [0.1, 0.2]),
        ([1, 2], [0.1, np.nan]),
        ([1], [0.1, 0.2]),
    ],
)
def test_forecast_hash_rejects_noncanonical_vectors(stamps, forecasts):
    with pytest.raises(PSR01BError):
        forecast_vector_sha256(stamps, forecasts)


def test_cost_aware_rule_suppresses_small_switch_and_charges_terminal_liquidation():
    forecasts = [[0.001, 0.003, 0.003]]
    realized = [[0.0, 0.0, 0.0]]

    baseline = evaluate_strategy_segments(forecasts, realized, rule="BASELINE_SIGN")
    aware = evaluate_strategy_segments(forecasts, realized, rule="COST_AWARE")

    # Baseline enters immediately then is forcibly liquidated at segment/fold end.
    np.testing.assert_array_equal(baseline.positions, [1, 1, 1])
    assert baseline.turnover == 2
    assert baseline.completed_trades == 1
    assert baseline.returns.sum() == pytest.approx(-0.002)

    # 0.001 is below the 2*c hurdle from cash; 0.003 enters on the next row.
    np.testing.assert_array_equal(aware.positions, [0, 1, 1])
    assert aware.turnover == 2
    assert aware.completed_trades == 1
    assert aware.returns.sum() == pytest.approx(-0.002)


def test_segments_force_flat_restart_and_do_not_carry_positions_across_gap():
    forecasts = [[0.01, 0.01], [0.01, 0.01]]
    realized = [[0.0, 0.0], [0.0, 0.0]]
    out = evaluate_strategy_segments(forecasts, realized, rule="BASELINE_SIGN")
    # Each segment starts from cash, enters, then liquidates.
    assert out.turnover == 4
    assert out.completed_trades == 2
    np.testing.assert_array_equal(out.positions, [1, 1, 1, 1])
    assert out.returns.sum() == pytest.approx(-0.004)


def test_performance_metrics_match_direct_wealth_oracle():
    returns = np.array([0.01, -0.02, 0.03], dtype=float)
    got = performance_metrics(returns)
    wealth = np.cumprod(1 + returns)
    expected_total = wealth[-1] - 1
    expected_arc = wealth[-1] ** (8760 / 3) - 1
    expected_asd = np.sqrt(8760) * np.std(returns, ddof=1)
    equity = np.r_[1.0, wealth]
    expected_mdd = np.min(equity / np.maximum.accumulate(equity) - 1)
    assert got["total_return"] == pytest.approx(expected_total)
    assert got["ARC"] == pytest.approx(expected_arc)
    assert got["ASD"] == pytest.approx(expected_asd)
    assert got["max_drawdown"] == pytest.approx(expected_mdd)


def test_metrics_fail_closed_if_wealth_nonpositive():
    with pytest.raises(PSR01BError):
        performance_metrics([0.0, -1.0])


def test_holm_two_registered_order_breaks_exact_ties():
    out = holm_two({"PAPER_FILL": 0.02, "PROJECT_GAP_PRESERVING": 0.02})
    assert out["PAPER_FILL"]["adjusted_p"] == pytest.approx(0.04)
    assert out["PROJECT_GAP_PRESERVING"]["adjusted_p"] == pytest.approx(0.04)
    assert out["PAPER_FILL"]["reject"]
    assert out["PROJECT_GAP_PRESERVING"]["reject"]


def test_bootstrap_excludes_short_segments_and_is_deterministic():
    # Two eligible 48-row segments for L=24 plus one short descriptive-only segment.
    b = [np.zeros(48), np.zeros(48), np.zeros(20)]
    c = [np.full(48, 0.001), np.full(48, 0.001), np.full(20, -0.001)]
    a = paired_segment_bootstrap(b, c, block_hours=24, arm_index=0, draws=64)
    z = paired_segment_bootstrap(b, c, block_hours=24, arm_index=0, draws=64)
    assert a == z
    assert a.available
    assert a.eligible_segments == 2
    assert a.inference_universe_mean == pytest.approx(0.001)
    expected_all = (96 * 0.001 - 20 * 0.001) / 116
    assert a.all_record_mean == pytest.approx(expected_all)
    assert a.p_value == pytest.approx(1 / 65)
    assert a.ci_95 == pytest.approx((0.001, 0.001))
    # Constant strategy-return vectors make Sharpe complementary evidence
    # unavailable rather than silently inventing a value.
    assert not a.sharpe_difference_available
    assert a.observed_inference_sharpe_difference is None
    assert a.sharpe_difference_ci_95 is None
    assert seed_from_coordinates(BOOTSTRAP_ROOT, 24, 0) != seed_from_coordinates(
        BOOTSTRAP_ROOT, 24, 1
    )


def test_bootstrap_unavailable_with_fewer_than_two_inference_segments():
    out = paired_segment_bootstrap(
        [np.zeros(48), np.zeros(47)],
        [np.ones(48) * 0.001, np.ones(47) * 0.001],
        block_hours=24,
        arm_index=1,
        draws=8,
    )
    assert not out.available
    assert out.eligible_segments == 1
    assert out.p_value is None
    assert out.ci_95 is None
    assert not out.sharpe_difference_available
    assert out.observed_inference_sharpe_difference is None
    assert out.sharpe_difference_ci_95 is None


def test_bootstrap_sharpe_uses_identical_paired_sample_indices(monkeypatch):
    # L=24 requires n>=48.  Two eligible synthetic segments are used.
    n = 48
    x = np.arange(n, dtype=float)
    baseline = [
        1e-5 * np.sin(x / 3.0),
        1e-5 * np.cos(x / 4.0),
    ]
    cost_aware = [
        baseline[0] + 2e-6 * np.sin(x / 5.0) + 5e-7,
        baseline[1] + 2e-6 * np.cos(x / 6.0) + 5e-7,
    ]

    calls = []

    def fixed_indices(rng, length, block_length):
        assert length == n
        assert block_length == 24
        calls.append((length, block_length))
        # Deliberately repeat a subset so the bootstrap Sharpe differs from the
        # observed value.  The implementation must apply this one index vector
        # to baseline and cost-aware returns together.
        return np.tile(np.arange(24), 2)

    monkeypatch.setattr(coremod, "_circular_indices", fixed_indices)
    out = paired_segment_bootstrap(
        baseline,
        cost_aware,
        block_hours=24,
        arm_index=0,
        draws=1,
    )

    # One index draw per segment, not separate RNG/index draws for each strategy.
    assert calls == [(n, 24), (n, 24)]
    assert out.sharpe_difference_available

    idx = np.tile(np.arange(24), 2)
    sampled_b = np.concatenate([segment[idx] for segment in baseline])
    sampled_c = np.concatenate([segment[idx] for segment in cost_aware])
    expected = (
        performance_metrics(sampled_c)["SHARPE"]
        - performance_metrics(sampled_b)["SHARPE"]
    )
    assert out.sharpe_difference_ci_95 == pytest.approx((expected, expected))

    observed_b = np.concatenate(baseline)
    observed_c = np.concatenate(cost_aware)
    observed_expected = (
        performance_metrics(observed_c)["SHARPE"]
        - performance_metrics(observed_b)["SHARPE"]
    )
    assert out.observed_inference_sharpe_difference == pytest.approx(observed_expected)


def _passing_arm(p):
    return {
        "all_record_mean": 0.001,
        "inference_universe_mean": 0.001,
        "eligible_primary_segments": 2,
        "primary_p_value": p,
        "cost_aware_turnover": 9,
        "baseline_turnover": 10,
        "cost_aware_completed_trades": 20,
        "cost_aware_sharpe": 1.1,
        "baseline_sharpe": 1.0,
    }


def test_success_requires_all_seven_conditions_in_both_arms():
    arms = {
        "PAPER_FILL": _passing_arm(0.01),
        "PROJECT_GAP_PRESERVING": _passing_arm(0.02),
    }
    assert classify_success(arms) == "BOUNDED_H2_REPLICATION"

    failed = {k: dict(v) for k, v in arms.items()}
    failed["PROJECT_GAP_PRESERVING"]["cost_aware_completed_trades"] = 19
    assert classify_success(failed) == "BOUNDED_H2_NOT_REPLICATED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("inference_universe_mean", None),
        ("primary_p_value", None),
        ("cost_aware_sharpe", None),
        ("baseline_sharpe", None),
    ],
)
def test_success_classifier_unavailable_required_evidence_fails_closed(field, value):
    arms = {
        "PAPER_FILL": _passing_arm(0.01),
        "PROJECT_GAP_PRESERVING": _passing_arm(0.02),
    }
    arms["PAPER_FILL"][field] = value
    assert classify_success(arms) == "BOUNDED_H2_NOT_REPLICATED"


def test_success_classifier_insufficient_primary_segments_fails_closed_before_p_value_cast():
    arms = {
        "PAPER_FILL": _passing_arm(0.01),
        "PROJECT_GAP_PRESERVING": _passing_arm(0.02),
    }
    arms["PAPER_FILL"]["eligible_primary_segments"] = 1
    arms["PAPER_FILL"]["primary_p_value"] = None
    arms["PAPER_FILL"]["inference_universe_mean"] = None
    assert classify_success(arms) == "BOUNDED_H2_NOT_REPLICATED"
