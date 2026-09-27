"""Synthetic tests for PSR-01B missing-data arms and OHLCV features."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import numpy as np
import pytest

from research_core.data_interfaces import MarketBar
from research_core.psr01b_core import PSR01BError
from research_core.psr01b_features import (
    BASE_FEATURE_NAMES,
    clip_to_artificial_state_boundary,
    compute_base_ohlcv_features,
    construct_missing_data_arm,
    warmup_start,
)


UTC = timezone.utc
START = datetime(2021, 1, 1, tzinfo=UTC)


def bar(hour: int, close: float, volume: float = 10.0, *, flat: bool = False) -> MarketBar:
    stamp = START + timedelta(hours=hour)
    c = Decimal(str(close))
    v = Decimal(str(volume))
    if flat:
        o = h = l = c
    else:
        o = Decimal(str(close - 0.2))
        h = Decimal(str(close + 0.5))
        l = Decimal(str(close - 0.5))
    return MarketBar(stamp, "BTCUSDT", o, h, l, c, v)


def test_paper_fill_inserts_flat_zero_volume_bar_with_provenance():
    observed = [bar(0, 100), bar(2, 102)]
    arm = construct_missing_data_arm(
        observed,
        arm="PAPER_FILL",
        interval_start=START,
        interval_end_exclusive=START + timedelta(hours=3),
    )
    assert len(arm.bars) == 3
    assert arm.synthetic == (False, True, False)
    fill = arm.bars[1]
    assert fill.open == fill.high == fill.low == fill.close == observed[0].close
    assert fill.volume == Decimal("0")
    assert arm.segment_ids == (0, 0, 0)
    assert arm.segment_indices == (0, 1, 2)


def test_paper_fill_rejects_leading_gap():
    with pytest.raises(PSR01BError, match="leading gap"):
        construct_missing_data_arm(
            [bar(1, 101)],
            arm="PAPER_FILL",
            interval_start=START,
            interval_end_exclusive=START + timedelta(hours=2),
        )


def test_gap_preserving_keeps_accepted_rows_and_resets_segment_state():
    observed = [bar(0, 100), bar(1, 101), bar(3, 103), bar(4, 104)]
    arm = construct_missing_data_arm(
        observed,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=START,
        interval_end_exclusive=START + timedelta(hours=5),
    )
    assert arm.bars == tuple(observed)
    assert arm.synthetic == (False, False, False, False)
    assert arm.segment_ids == (0, 0, 1, 1)
    assert arm.segment_indices == (0, 1, 0, 1)


def test_first_fold_warmup_boundary_is_exactly_744_hours():
    train = datetime(2018, 1, 1, tzinfo=UTC)
    assert warmup_start(train) == datetime(2017, 12, 1, tzinfo=UTC)


def test_artificial_state_boundary_discards_all_earlier_bars():
    train = START + timedelta(hours=744)
    bars = [bar(i, 100 + i * 0.01) for i in range(800)]
    clipped = clip_to_artificial_state_boundary(
        bars,
        train_start=train,
        through_exclusive=START + timedelta(hours=780),
    )
    assert clipped[0].timestamp == START
    assert clipped[-1].timestamp == START + timedelta(hours=779)


def test_non_utc_timestamp_is_rejected_even_if_timezone_aware():
    tz = timezone(timedelta(hours=-5))
    bad = MarketBar(
        datetime(2021, 1, 1, tzinfo=tz),
        "BTCUSDT",
        Decimal("99"),
        Decimal("101"),
        Decimal("98"),
        Decimal("100"),
        Decimal("10"),
    )
    with pytest.raises(PSR01BError, match="must be UTC"):
        construct_missing_data_arm(
            [bad],
            arm="PROJECT_GAP_PRESERVING",
            interval_start=START,
            interval_end_exclusive=START + timedelta(hours=1),
        )


def test_base_feature_order_and_first_global_deployable_origin():
    observed = [bar(i, 100 + 0.01 * i, 10 + (i % 7)) for i in range(337)]
    arm = construct_missing_data_arm(
        observed,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=START,
        interval_end_exclusive=START + timedelta(hours=337),
    )
    features = compute_base_ohlcv_features(arm)
    assert features.names == BASE_FEATURE_NAMES
    assert features.matrix.shape == (337, 15)
    np.testing.assert_array_equal(np.flatnonzero(features.deployable), [336])
    assert np.isfinite(features.matrix[336]).all()


def test_base_feature_formulas_against_direct_oracle():
    observed = [bar(i, 100 + i, 1 + i) for i in range(337)]
    arm = construct_missing_data_arm(
        observed,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=START,
        interval_end_exclusive=START + timedelta(hours=337),
    )
    out = compute_base_ohlcv_features(arm)
    i = 336
    row = out.matrix[i]
    current = observed[i]
    previous = observed[i - 1]
    o, h, l, c, v = map(float, (current.open, current.high, current.low, current.close, current.volume))
    prev_c = float(previous.close)
    prev_v = float(previous.volume)
    tp = (h + l + c) / 3
    prev_tp = (float(previous.high) + float(previous.low) + float(previous.close)) / 3
    vol24 = np.mean([float(x.volume) for x in observed[i - 23 : i + 1]])

    assert row[0] == pytest.approx(np.log(c / prev_c))
    assert row[1] == pytest.approx(np.log(o / prev_c))
    assert row[2] == pytest.approx(np.log(h / prev_c))
    assert row[3] == pytest.approx(np.log(l / prev_c))
    assert row[4] == pytest.approx(np.log(c / o))
    assert row[5] == pytest.approx(np.log(h / l))
    assert row[6] == pytest.approx((2 * c - h - l) / (h - l))
    assert row[7] == pytest.approx((c - o) / (h - l))
    assert row[8] == pytest.approx((h - max(o, c)) / (h - l))
    assert row[9] == pytest.approx((min(o, c) - l) / (h - l))
    assert row[10] == pytest.approx(np.log1p(v))
    assert row[11] == pytest.approx(np.log((v + 1) / (prev_v + 1)))
    assert row[12] == pytest.approx(v / vol24 - 1)
    assert row[13] == pytest.approx(np.log1p(c * v))
    assert row[14] == pytest.approx(np.log(tp / prev_tp))


def test_flat_bar_fraction_features_are_exact_zero():
    observed = [bar(i, 100 + 0.01 * i, 0 if i == 336 else 10) for i in range(336)]
    observed.append(bar(336, 103.36, 0, flat=True))
    arm = construct_missing_data_arm(
        observed,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=START,
        interval_end_exclusive=START + timedelta(hours=337),
    )
    row = compute_base_ohlcv_features(arm).matrix[336]
    np.testing.assert_array_equal(row[[6, 7, 8, 9]], [0.0, 0.0, 0.0, 0.0])


def test_gap_resets_global_336_transition_eligibility():
    first = [bar(i, 100 + 0.01 * i) for i in range(337)]
    # One missing hour at 337. Second segment begins at 338 and has 337 bars.
    second = [bar(338 + i, 200 + 0.01 * i) for i in range(337)]
    observed = first + second
    arm = construct_missing_data_arm(
        observed,
        arm="PROJECT_GAP_PRESERVING",
        interval_start=START,
        interval_end_exclusive=START + timedelta(hours=675),
    )
    out = compute_base_ohlcv_features(arm)
    eligible = np.flatnonzero(out.deployable)
    assert eligible.tolist() == [336, 673]
    assert out.segment_indices[337] == 0
    assert out.segment_indices[673] == 336
