"""Synthetic/offline tests for PSR-01B 28-column matrix assembly."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import numpy as np
import pytest

from research_core.data_interfaces import MarketBar
from research_core.psr01b_egarch import replay_segment
from research_core.psr01b_features import ArmBars, BaseFeatureResult, BASE_FEATURE_NAMES
from research_core.psr01b_matrix import (
    DEPLOYED_FEATURE_NAMES,
    EGARCH_FEATURE_NAMES,
    SELECTED_FEATURE_NAMES,
    DeployedMatrixResult,
    EGARCHFeatureResult,
    SplitRows,
    assemble_deployed_matrix,
    build_egarch_features,
    eligible_split_rows,
    union_original_train_validation_rows,
)
from research_core.psr01b_ta import FeatureSelectionResult, GROUP_ORDER


UTC = timezone.utc
START = datetime(2021, 1, 1, tzinfo=UTC)


def make_bar(stamp, close):
    c = Decimal(str(close))
    return MarketBar(
        stamp,
        "BTCUSDT",
        c,
        c,
        c,
        c,
        Decimal("10"),
    )


def test_deployed_feature_registry_is_exactly_28_in_frozen_order():
    assert len(DEPLOYED_FEATURE_NAMES) == 28
    assert DEPLOYED_FEATURE_NAMES[:15] == BASE_FEATURE_NAMES
    assert DEPLOYED_FEATURE_NAMES[15:25] == SELECTED_FEATURE_NAMES
    assert DEPLOYED_FEATURE_NAMES[25:] == EGARCH_FEATURE_NAMES
    assert SELECTED_FEATURE_NAMES == tuple(
        f"SELECTED__{group}" for group in GROUP_ORDER
    )


def dummy_selection(n):
    selected_by_group = {
        group: f"DUMMY__{group}" for group in GROUP_ORDER
    }
    selected_names = tuple(selected_by_group[group] for group in GROUP_ORDER)
    selected_matrix = np.arange(n * 10, dtype=float).reshape(n, 10) + 100.0
    return FeatureSelectionResult(
        selected_by_group,
        selected_names,
        selected_matrix,
        {group: {} for group in GROUP_ORDER},
        {},
    )


def test_matrix_assembly_preserves_exact_column_blocks_and_deployability():
    n = 3
    base_matrix = np.arange(n * 15, dtype=float).reshape(n, 15)
    base = BaseFeatureResult(
        BASE_FEATURE_NAMES,
        base_matrix,
        np.array([True, True, False]),
        np.zeros(n, dtype=int),
        np.arange(n),
    )
    selection = dummy_selection(n)
    egarch_matrix = np.arange(n * 3, dtype=float).reshape(n, 3) + 200.0
    egarch = EGARCHFeatureResult(
        egarch_matrix,
        np.array([True, False, True]),
    )

    out = assemble_deployed_matrix(
        base=base,
        selection=selection,
        egarch=egarch,
    )
    assert out.names == DEPLOYED_FEATURE_NAMES
    np.testing.assert_array_equal(out.matrix[:, :15], base_matrix)
    np.testing.assert_array_equal(out.matrix[:, 15:25], selection.selected_matrix)
    np.testing.assert_array_equal(out.matrix[:, 25:], egarch_matrix)
    np.testing.assert_array_equal(out.deployable, [True, False, False])


def test_egarch_replay_includes_return_ending_at_training_start_and_resets_after_gap():
    stamps = [
        START - timedelta(hours=1),
        START,
        START + timedelta(hours=1),
        START + timedelta(hours=3),
        START + timedelta(hours=4),
        START + timedelta(hours=5),
    ]
    closes = [100.0, 101.0, 102.0, 200.0, 202.0, 204.0]
    bars = tuple(make_bar(t, c) for t, c in zip(stamps, closes))
    arm = ArmBars(
        "PROJECT_GAP_PRESERVING",
        bars,
        (False,) * 6,
        (0, 0, 0, 1, 1, 1),
        (0, 1, 2, 0, 1, 2),
    )
    params = np.array([0.0, -0.1, 0.1, 0.0, 0.8, 8.0])
    got = build_egarch_features(
        arm,
        replay_start=START,
        params=params,
        order=(1, 1, 1),
    )

    first_y = [
        100 * np.log(101.0 / 100.0),
        100 * np.log(102.0 / 101.0),
    ]
    second_y = [
        100 * np.log(202.0 / 200.0),
        100 * np.log(204.0 / 202.0),
    ]
    first = replay_segment(first_y, params, (1, 1, 1))
    second = replay_segment(second_y, params, (1, 1, 1))

    assert not got.finite[0]
    np.testing.assert_allclose(got.matrix[1:3, 0], first.sigma_next)
    np.testing.assert_allclose(got.matrix[1:3, 1], first.log_sigma_next)
    np.testing.assert_allclose(got.matrix[1:3, 2], first.z_current)

    # First post-gap bar has no contiguous predecessor return and stays unavailable.
    assert not got.finite[3]
    np.testing.assert_allclose(got.matrix[4:6, 0], second.sigma_next)
    np.testing.assert_allclose(got.matrix[4:6, 1], second.log_sigma_next)
    np.testing.assert_allclose(got.matrix[4:6, 2], second.z_current)


def test_split_endpoint_rule_last_origin_is_E_minus_2h_and_nan_target_is_excluded():
    bars = tuple(make_bar(START + timedelta(hours=i), 100 + i) for i in range(5))
    arm = ArmBars(
        "PAPER_FILL",
        bars,
        (False,) * 5,
        (0,) * 5,
        tuple(range(5)),
    )
    matrix = np.ones((5, 28), dtype=float)
    deployed = DeployedMatrixResult(
        DEPLOYED_FEATURE_NAMES,
        matrix,
        np.ones(5, dtype=bool),
    )
    targets = np.array([0.1, 0.2, np.nan, 0.4, np.nan])
    rows = eligible_split_rows(
        arm,
        deployed,
        targets,
        split_start=START,
        split_end=START + timedelta(hours=4),
    )
    # t=0 and t=1 qualify; t=2 has a missing target; t=3 would cross E.
    np.testing.assert_array_equal(rows.indices, [0, 1])
    assert rows.origin_timestamps == (
        START,
        START + timedelta(hours=1),
    )


def test_boundary_crossing_train_row_is_not_resurrected_by_union():
    train = SplitRows(
        np.array([1, 2]),
        np.ones((2, 28)),
        np.array([0.1, 0.2]),
        (START, START + timedelta(hours=1)),
    )
    validation = SplitRows(
        np.array([4, 5]),
        np.full((2, 28), 2.0),
        np.array([0.3, 0.4]),
        (START + timedelta(hours=3), START + timedelta(hours=4)),
    )
    X, y = union_original_train_validation_rows(train, validation)
    assert X.shape == (4, 28)
    np.testing.assert_array_equal(y, [0.1, 0.2, 0.3, 0.4])
    np.testing.assert_array_equal(X[:2], 1.0)
    np.testing.assert_array_equal(X[2:], 2.0)


def test_matrix_assembly_rejects_selected_group_order_drift():
    base = BaseFeatureResult(
        BASE_FEATURE_NAMES,
        np.ones((1, 15)),
        np.array([True]),
        np.array([0]),
        np.array([336]),
    )
    selection = dummy_selection(1)
    bad = FeatureSelectionResult(
        selection.selected_by_group,
        tuple(reversed(selection.selected_names)),
        selection.selected_matrix,
        selection.average_ranks,
        selection.block_correlations,
    )
    egarch = EGARCHFeatureResult(np.ones((1, 3)), np.array([True]))
    with pytest.raises(Exception, match="selected TA group order"):
        assemble_deployed_matrix(base=base, selection=bad, egarch=egarch)
