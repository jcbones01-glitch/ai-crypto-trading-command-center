"""Synthetic/offline tests for PSR-01B TA candidates and selector."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import numpy as np
import pytest

from research_core.data_interfaces import MarketBar
from research_core.psr01b_core import PSR01BError
from research_core.psr01b_features import ArmBars, construct_missing_data_arm
from research_core.psr01b_ta import (
    CANDIDATE_FAMILIES,
    CANDIDATE_NAMES,
    GROUPS,
    GROUP_ORDER,
    TACandidateResult,
    compute_ta_candidates,
    select_four_block_features,
    select_group_from_block_correlations,
    spearman_block_correlation,
)


UTC = timezone.utc
START = datetime(2020, 1, 1, tzinfo=UTC)


def bar(stamp: datetime, close: float, volume: float = 10.0) -> MarketBar:
    c = Decimal(str(close))
    return MarketBar(
        stamp,
        "BTCUSDT",
        Decimal(str(close - 0.2)),
        Decimal(str(close + 0.5)),
        Decimal(str(close - 0.5)),
        c,
        Decimal(str(volume)),
    )


def hourly_bars(start: datetime, n: int, *, offset: float = 0.0):
    return [
        bar(start + timedelta(hours=i), 100.0 + offset + 0.01 * i, 10.0 + (i % 11))
        for i in range(n)
    ]


def test_candidate_registry_is_exactly_94_unique_canonical_names():
    assert len(CANDIDATE_NAMES) == 94
    assert len(CANDIDATE_FAMILIES) == 94
    assert len(set(CANDIDATE_NAMES)) == 94
    assert CANDIDATE_NAMES[0] == "RSI__W3"
    assert CANDIDATE_NAMES[-1] == "LAG_RETURN__K24"
    assert set(GROUP_ORDER) == set(GROUPS)


def test_core_ta_formulas_against_direct_small_oracles():
    observed = [
        bar(START + timedelta(hours=i), 100.0 + i, 10.0)
        for i in range(4)
    ]
    arm = construct_missing_data_arm(
        observed,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=START,
        interval_end_exclusive=START + timedelta(hours=4),
    )
    out = compute_ta_candidates(arm)
    col = {name: i for i, name in enumerate(out.names)}

    # w=3 values
    assert out.matrix[3, col["RSI__W3"]] == pytest.approx(100.0)
    assert out.matrix[3, col["ROC__W3"]] == pytest.approx(103.0 / 100.0 - 1.0)
    assert out.matrix[2, col["DIST_SMA__W3"]] == pytest.approx(
        102.0 / np.mean([100.0, 101.0, 102.0]) - 1.0
    )

    logs = np.log(np.array([101 / 100, 102 / 101, 103 / 102], dtype=float))
    assert out.matrix[3, col["ROLL_STD__W3"]] == pytest.approx(np.std(logs, ddof=0))

    closes = np.array([100.0, 101.0, 102.0])
    expected_bb = (102.0 - closes.mean()) / (2.0 * closes.std(ddof=0))
    assert out.matrix[2, col["BB_POS__W3"]] == pytest.approx(expected_bb)

    typical = np.array([100.0, 101.0, 102.0])
    expected_vwap = typical.mean()
    assert out.matrix[2, col["VWAP_DEV__W3"]] == pytest.approx(102.0 / expected_vwap - 1.0)

    # TR is 1.5 on each post-first row for this fixture.
    assert out.matrix[3, col["ATR_RATIO__W3"]] == pytest.approx(1.5 / 103.0)

    # Strictly rising typical price makes all three classified MFI flows positive.
    assert out.matrix[3, col["MFI__W3"]] == pytest.approx(1.0)

    # OBV over rows 0..2 is [0,10,20]; OLS slope=10, mean volume=10.
    assert out.matrix[2, col["OBV_SLOPE__W3"]] == pytest.approx(1.0)

    assert out.matrix[3, col["LAG_RETURN__K3"]] == pytest.approx(np.log(103.0 / 100.0))


def test_macd_and_histogram_use_unadjusted_recursive_emas():
    observed = [
        bar(START + timedelta(hours=i), close, 10.0)
        for i, close in enumerate([100.0, 102.0, 101.0, 104.0])
    ]
    arm = construct_missing_data_arm(
        observed,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=START,
        interval_end_exclusive=START + timedelta(hours=4),
    )
    out = compute_ta_candidates(arm)
    col = {name: i for i, name in enumerate(out.names)}

    close = np.array([100.0, 102.0, 101.0, 104.0])
    def ema(values, span):
        alpha = 2 / (span + 1)
        z = np.empty(len(values))
        z[0] = values[0]
        for i in range(1, len(values)):
            z[i] = alpha * values[i] + (1 - alpha) * z[i - 1]
        return z

    raw = ema(close, 2) - ema(close, 3)
    signal = ema(raw, 2)
    np.testing.assert_allclose(
        out.matrix[:, col["MACD__W3"]], raw / close, atol=1e-15
    )
    np.testing.assert_allclose(
        out.matrix[:, col["MACD_HIST__W3"]], (raw - signal) / close, atol=1e-15
    )


def test_all_94_candidates_are_finite_at_first_deployable_origin():
    bars = hourly_bars(START, 337)
    arm = construct_missing_data_arm(
        bars,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=START,
        interval_end_exclusive=START + timedelta(hours=337),
    )
    out = compute_ta_candidates(arm)
    assert out.matrix.shape == (337, 94)
    np.testing.assert_array_equal(np.flatnonzero(out.deployable), [336])
    assert np.isfinite(out.matrix[336]).all()
    assert np.isfinite(out.target_next_hour[:336]).all()
    assert np.isnan(out.target_next_hour[336])


def test_gap_resets_every_candidate_state_and_deployability():
    first = hourly_bars(START, 337)
    second_start = START + timedelta(hours=338)
    second = hourly_bars(second_start, 337, offset=50.0)
    observed = first + second
    arm = construct_missing_data_arm(
        observed,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=START,
        interval_end_exclusive=START + timedelta(hours=675),
    )
    out = compute_ta_candidates(arm)
    eligible = np.flatnonzero(out.deployable)
    assert eligible.tolist() == [336, 673]

    col = {name: i for i, name in enumerate(out.names)}
    second_first = 337
    assert np.isnan(out.matrix[second_first, col["RSI__W3"]])
    assert np.isnan(out.matrix[second_first, col["LAG_RETURN__K1"]])
    # MACD exists recursively from segment j=0, but cannot deploy yet.
    assert np.isfinite(out.matrix[second_first, col["MACD__W3"]])
    assert not out.deployable[second_first]
    assert np.isfinite(out.matrix[673]).all()


def test_target_never_crosses_a_gap():
    observed = hourly_bars(START, 2) + hourly_bars(START + timedelta(hours=3), 2, offset=10)
    arm = construct_missing_data_arm(
        observed,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=START,
        interval_end_exclusive=START + timedelta(hours=5),
    )
    out = compute_ta_candidates(arm)
    assert np.isfinite(out.target_next_hour[0])
    assert np.isnan(out.target_next_hour[1])
    assert np.isfinite(out.target_next_hour[2])
    assert np.isnan(out.target_next_hour[3])


def test_spearman_requires_100_finite_pairs_and_rejects_constant_candidate():
    x = np.arange(99, dtype=float)
    y = x.copy()
    assert spearman_block_correlation(x, y) is None

    x = np.arange(100, dtype=float)
    y = x[::-1]
    assert spearman_block_correlation(x, y) == pytest.approx(-1.0)

    assert spearman_block_correlation(np.ones(100), np.arange(100.0)) is None


def test_common_four_block_universe_is_built_before_ranking():
    correlations = {
        "A": (0.9, 0.1, 0.1, 0.1),
        "B": (0.8, 0.8, 0.8, 0.8),
        # C would rank first in some blocks but is ineligible in block 4,
        # so it must be excluded from every block's rank universe.
        "C": (0.99, 0.99, 0.01, None),
    }
    winner, ranks = select_group_from_block_correlations(["A", "B", "C"], correlations)
    assert winner == "B"
    assert set(ranks) == {"A", "B"}
    assert ranks["B"] < ranks["A"]


def test_ascii_lexical_name_breaks_exact_rank_ties():
    correlations = {
        "AAA": (0.5, 0.5, 0.5, 0.5),
        "BBB": (0.5, 0.5, 0.5, 0.5),
    }
    winner, ranks = select_group_from_block_correlations(["BBB", "AAA"], correlations)
    assert winner == "AAA"
    assert ranks["AAA"] == 1.0
    assert ranks["BBB"] == 2.0


def test_full_four_calendar_block_selector_uses_registered_groups_and_returns_10():
    train_start = datetime(2020, 1, 1, tzinfo=UTC)
    train_end = datetime(2021, 1, 1, tzinfo=UTC)
    quarter_starts = [
        datetime(2020, 1, 1, tzinfo=UTC),
        datetime(2020, 4, 1, tzinfo=UTC),
        datetime(2020, 7, 1, tzinfo=UTC),
        datetime(2020, 10, 1, tzinfo=UTC),
    ]
    observed = []
    for q, start in enumerate(quarter_starts):
        observed.extend(hourly_bars(start, 120, offset=10.0 * q))

    arm = construct_missing_data_arm(
        observed,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=train_start,
        interval_end_exclusive=train_end,
    )
    n = len(arm.bars)
    target = np.tile(np.arange(120, dtype=float), 4)
    matrix = np.column_stack(
        [target + (i + 1) * 1e-9 for i in range(len(CANDIDATE_NAMES))]
    )
    candidates = TACandidateResult(
        CANDIDATE_NAMES,
        CANDIDATE_FAMILIES,
        matrix,
        target,
        np.ones(n, dtype=bool),
    )
    result = select_four_block_features(
        arm,
        candidates,
        train_start=train_start,
        train_end=train_end,
    )
    assert tuple(result.selected_by_group) == GROUP_ORDER
    assert len(result.selected_names) == 10
    assert result.selected_matrix.shape == (n, 10)

    # With equal absolute Spearman correlations, lexical candidate name wins
    # within each registered group's common four-block universe.
    for group in GROUP_ORDER:
        allowed = set(GROUPS[group])
        names = sorted(
            name
            for name, family in zip(CANDIDATE_NAMES, CANDIDATE_FAMILIES)
            if family in allowed
        )
        assert result.selected_by_group[group] == names[0]



def test_training_gap_first_336_transitions_cannot_influence_feature_selection():
    train_start = datetime(2020, 1, 1, tzinfo=UTC)
    train_end = datetime(2021, 1, 1, tzinfo=UTC)

    # Synthetic training observations include a real gap inside Q1 and separate
    # contiguous segments in each later quarter. Every block still has >100
    # globally eligible rows after the registered 336-transition rebuild.
    chunks = [
        hourly_bars(datetime(2020, 1, 1, tzinfo=UTC), 400, offset=0.0),
        hourly_bars(datetime(2020, 1, 17, 17, tzinfo=UTC), 500, offset=20.0),
        hourly_bars(datetime(2020, 4, 1, tzinfo=UTC), 500, offset=40.0),
        hourly_bars(datetime(2020, 7, 1, tzinfo=UTC), 500, offset=60.0),
        hourly_bars(datetime(2020, 10, 1, tzinfo=UTC), 500, offset=80.0),
    ]
    observed = [item for chunk in chunks for item in chunk]
    arm = construct_missing_data_arm(
        observed,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=train_start,
        interval_end_exclusive=train_end,
    )
    deployable = np.asarray(arm.segment_indices) >= 336

    # Confirm the post-gap recovery interval exists and is globally forbidden.
    second_segment = np.flatnonzero(np.asarray(arm.segment_ids) == 1)
    assert len(second_segment) >= 337
    assert not deployable[second_segment[:336]].any()
    assert deployable[second_segment[336]]

    rng = np.random.default_rng(20260925)
    n = len(arm.bars)
    target = rng.normal(size=n)
    matrix = np.column_stack(
        [
            target + rng.normal(scale=0.05 + 0.001 * i, size=n)
            for i in range(len(CANDIDATE_NAMES))
        ]
    )
    original = TACandidateResult(
        CANDIDATE_NAMES,
        CANDIDATE_FAMILIES,
        matrix,
        target,
        deployable,
    )

    # Change only globally forbidden rows enough that they would materially alter
    # correlations if the selector accidentally used them.
    altered_matrix = matrix.copy()
    forbidden = ~deployable
    altered_matrix[forbidden] = rng.normal(
        loc=0.0,
        scale=1000.0,
        size=(int(np.count_nonzero(forbidden)), len(CANDIDATE_NAMES)),
    )
    altered = TACandidateResult(
        CANDIDATE_NAMES,
        CANDIDATE_FAMILIES,
        altered_matrix,
        target,
        deployable,
    )

    a = select_four_block_features(
        arm,
        original,
        train_start=train_start,
        train_end=train_end,
    )
    b = select_four_block_features(
        arm,
        altered,
        train_start=train_start,
        train_end=train_end,
    )

    assert a.selected_names == b.selected_names
    assert a.block_correlations == b.block_correlations


def test_selector_hard_fails_when_any_group_has_no_four_block_eligible_candidate():
    with pytest.raises(PSR01BError, match="no common-four-block"):
        select_group_from_block_correlations(
            ["A", "B"],
            {"A": (0.1, 0.1, None, 0.1), "B": (None, 0.2, 0.2, 0.2)},
        )
