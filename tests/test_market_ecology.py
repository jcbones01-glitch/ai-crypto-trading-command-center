from __future__ import annotations

from decimal import Decimal

import pytest

from research_core.market_ecology import (
    HOUR_US,
    FundingPoint,
    FuturesPoint,
    MarketEcologyError,
    SpotPoint,
    build_eco_deriv_rows,
    canonical_decimal,
    feature_identity,
    iso_to_epoch_us,
    log_basis,
)


BOUNDARY = iso_to_epoch_us("2022-01-01T00:00:00.000Z")


def test_log_basis_zero_and_positive_prices_only():
    assert canonical_decimal(log_basis(Decimal("100"), Decimal("100"))) == "0"
    assert log_basis(Decimal("100"), Decimal("101")) > 0
    assert log_basis(Decimal("100"), Decimal("99")) < 0
    with pytest.raises(MarketEcologyError):
        log_basis(Decimal("0"), Decimal("100"))


def test_funding_five_milliseconds_after_hour_is_not_visible_until_next_hour():
    open0 = iso_to_epoch_us("2021-01-01T07:00:00.000Z")
    open1 = iso_to_epoch_us("2021-01-01T08:00:00.000Z")
    funding_before = FundingPoint(
        iso_to_epoch_us("2021-01-01T00:00:00.002Z"),
        Decimal("0.0001"),
        Decimal("8"),
        "2021-01-01T00:00:00.002Z",
    )
    funding_after_decision = FundingPoint(
        iso_to_epoch_us("2021-01-01T08:00:00.005Z"),
        Decimal("0.0002"),
        Decimal("8"),
        "2021-01-01T08:00:00.005Z",
    )
    spot = [
        SpotPoint(open0, Decimal("100")),
        SpotPoint(open1, Decimal("101")),
    ]
    futures = [
        FuturesPoint(open0, Decimal("100.5")),
        FuturesPoint(open1, Decimal("101.5")),
    ]

    rows, _ = build_eco_deriv_rows(
        "BTCUSDT", spot, futures, [funding_before, funding_after_decision], BOUNDARY
    )

    # 07:00 bar is available at exactly 08:00, before the 08:00:00.005 funding event.
    assert rows[0]["feature_available_at"] == "2021-01-01T08:00:00.000Z"
    assert rows[0]["last_funding_calc_time"] == "2021-01-01T00:00:00.002Z"

    # 08:00 bar is available at 09:00, so the millisecond-delayed event is now visible.
    assert rows[1]["feature_available_at"] == "2021-01-01T09:00:00.000Z"
    assert rows[1]["last_funding_calc_time"] == "2021-01-01T08:00:00.005Z"


def test_exact_funding_at_feature_time_is_visible():
    open0 = iso_to_epoch_us("2021-01-01T07:00:00.000Z")
    funding = FundingPoint(
        iso_to_epoch_us("2021-01-01T08:00:00.000Z"),
        Decimal("0.0001"),
        Decimal("8"),
        "2021-01-01T08:00:00.000Z",
    )
    rows, _ = build_eco_deriv_rows(
        "BTCUSDT",
        [SpotPoint(open0, Decimal("100"))],
        [FuturesPoint(open0, Decimal("100"))],
        [funding],
        BOUNDARY,
    )
    assert rows[0]["last_funding_calc_time"] == "2021-01-01T08:00:00.000Z"
    assert rows[0]["funding_age_microseconds"] == 0


def test_protected_boundary_feature_is_never_emitted():
    last_open = iso_to_epoch_us("2021-12-31T23:00:00.000Z")
    funding = FundingPoint(
        iso_to_epoch_us("2021-12-31T16:00:00.000Z"),
        Decimal("0.0001"),
        Decimal("8"),
        "2021-12-31T16:00:00.000Z",
    )
    rows, diag = build_eco_deriv_rows(
        "ETHUSDT",
        [SpotPoint(last_open, Decimal("100"))],
        [FuturesPoint(last_open, Decimal("100"))],
        [funding],
        BOUNDARY,
    )
    assert rows == []
    assert diag["omitted_by_reason"]["feature_at_or_after_protected_boundary"] == 1


def test_missing_spot_exact_timestamp_is_omitted_not_forward_filled():
    open0 = iso_to_epoch_us("2021-01-01T00:00:00.000Z")
    funding = FundingPoint(
        iso_to_epoch_us("2021-01-01T00:00:00.000Z"),
        Decimal("0.0001"),
        Decimal("8"),
        "2021-01-01T00:00:00.000Z",
    )
    rows, diag = build_eco_deriv_rows(
        "BTCUSDT",
        [],
        [FuturesPoint(open0, Decimal("100"))],
        [funding],
        BOUNDARY,
    )
    assert rows == []
    assert diag["spot_futures_exact_timestamp_intersection_count"] == 0
    assert diag["omitted_by_reason"]["spot_unavailable_or_uncertified"] == 1


def test_future_mutation_cannot_change_earlier_feature():
    open0 = iso_to_epoch_us("2021-01-01T00:00:00.000Z")
    open1 = open0 + HOUR_US
    funding = FundingPoint(
        open0,
        Decimal("0.0001"),
        Decimal("8"),
        "2021-01-01T00:00:00.000Z",
    )
    spots = [SpotPoint(open0, Decimal("100")), SpotPoint(open1, Decimal("100"))]
    futures_a = [
        FuturesPoint(open0, Decimal("101")),
        FuturesPoint(open1, Decimal("102")),
    ]
    futures_b = [
        FuturesPoint(open0, Decimal("101")),
        FuturesPoint(open1, Decimal("999")),
    ]
    rows_a, _ = build_eco_deriv_rows("BTCUSDT", spots, futures_a, [funding], BOUNDARY)
    rows_b, _ = build_eco_deriv_rows("BTCUSDT", spots, futures_b, [funding], BOUNDARY)
    assert rows_a[0] == rows_b[0]
    assert rows_a[1] != rows_b[1]


def test_feature_identity_is_deterministic_and_content_sensitive():
    row = {
        "feature_available_at": "2021-01-01T01:00:00.000Z",
        "funding_age_microseconds": 0,
        "futures_close": "100",
        "last_funding_calc_time": "2021-01-01T00:00:00.000Z",
        "last_funding_interval_hours": "8",
        "last_funding_rate": "0.0001",
        "log_basis": "0",
        "spot_close": "100",
        "spot_open_time": "2021-01-01T00:00:00.000Z",
        "symbol": "BTCUSDT",
    }
    assert feature_identity([row]) == feature_identity([dict(row)])
    changed = dict(row)
    changed["last_funding_rate"] = "0.0002"
    assert feature_identity([row]) != feature_identity([changed])


def test_unsorted_or_duplicate_inputs_fail_closed():
    open0 = iso_to_epoch_us("2021-01-01T00:00:00.000Z")
    funding = FundingPoint(
        open0,
        Decimal("0.0001"),
        Decimal("8"),
        "2021-01-01T00:00:00.000Z",
    )
    with pytest.raises(MarketEcologyError):
        build_eco_deriv_rows(
            "BTCUSDT",
            [SpotPoint(open0, Decimal("100")), SpotPoint(open0, Decimal("101"))],
            [FuturesPoint(open0, Decimal("100"))],
            [funding],
            BOUNDARY,
        )
