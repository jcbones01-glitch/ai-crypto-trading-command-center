from __future__ import annotations

import io
import runpy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest


ROOT = Path(__file__).resolve().parents[1]
MOD = runpy.run_path(str(ROOT / "research/scripts/certify_cycle9_derivatives_development_v1.py"))


def zipped(name: str, text: str) -> bytes:
    output = io.BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(name, text)
    return output.getvalue()


def test_candidate_calendar_and_canonical_decimal():
    months = MOD["candidate_months"]()
    assert len(months) == 53
    assert months[0] == (2017, 8)
    assert months[-1] == (2021, 12)
    assert MOD["canonical_decimal"]("1.2300") == "1.23"
    assert MOD["canonical_decimal"]("0.00010000") == "0.0001"
    assert MOD["canonical_decimal"]("-0.000") == "0"
    with pytest.raises(MOD["CertificationError"]):
        MOD["canonical_decimal"]("NaN")


def test_timestamp_precision_is_preserved():
    text, unit, us = MOD["canonical_timestamp"]("1609459200002")
    assert text == "2021-01-01T00:00:00.002Z"
    assert unit == "milliseconds"
    assert us == 1609459200002000

    text, unit, us = MOD["canonical_timestamp"]("1609459200002003")
    assert text == "2021-01-01T00:00:00.002003Z"
    assert unit == "microseconds"
    assert us == 1609459200002003


def test_kline_archive_normalizes_without_binary_float():
    rows = [
        "1609459200000,29000.00,29100.000,28900.00,29050.5000,12.3400,1609462799999,358000.00,123,6.1000,177000.00,0",
        "1609462800000,29050.5000,29200.00,29000.00,29150.00,10.000,1609466399999,291500.0,100,5.0,145750.0,0",
    ]
    payload = zipped("BTCUSDT-1h-2021-01.csv", "\n".join(rows) + "\n")
    validation, normalized = MOD["validate_kline_archive"](
        payload, "BTCUSDT", "a" * 64
    )
    assert validation["raw_row_count"] == 2
    assert validation["header"] is None
    assert validation["timestamp_units"] == ["milliseconds"]
    assert normalized[0]["open"] == "29000"
    assert normalized[0]["close"] == "29050.5"
    assert normalized[0]["volume"] == "12.34"
    assert normalized[0]["open_time"] == "2021-01-01T00:00:00.000Z"
    assert normalized[1]["open_time"] == "2021-01-01T01:00:00.000Z"


def test_kline_header_and_bad_hour_fail_closed():
    header = ",".join(MOD["KLINE_FIELDS"])
    payload = zipped("x.csv", header + "\n")
    with pytest.raises(MOD["CertificationError"]):
        MOD["validate_kline_archive"](payload, "BTCUSDT", "b" * 64)

    bad = "1609459200001,1,1,1,1,1,1609462799999,1,1,1,1,0\n"
    payload = zipped("x.csv", bad)
    with pytest.raises(MOD["CertificationError"]):
        MOD["validate_kline_archive"](payload, "BTCUSDT", "b" * 64)


def test_funding_millisecond_offsets_are_preserved_and_tolerated():
    text = (
        "calc_time,funding_interval_hours,last_funding_rate\n"
        "1609459200002,8,0.00010000\n"
        "1609488000000,8,-0.00005000\n"
        "1609516800005,8,0.00000000\n"
    )
    payload = zipped("BTCUSDT-fundingRate-2021-01.csv", text)
    validation, normalized = MOD["validate_funding_archive"](
        payload, "BTCUSDT", "c" * 64
    )
    assert validation["funding_interval_hours_observed"] == ["8"]
    assert normalized[0]["calc_time"] == "2021-01-01T00:00:00.002Z"
    assert normalized[1]["calc_time"] == "2021-01-01T08:00:00.000Z"
    assert normalized[0]["last_funding_rate"] == "0.0001"
    assert normalized[1]["last_funding_rate"] == "-0.00005"
    assert normalized[2]["last_funding_rate"] == "0"


def test_funding_spacing_over_one_second_fails_closed():
    # Second event is 8 hours + 1.001 seconds after the first.
    first = 1609459200000
    second = first + 8 * 60 * 60 * 1000 + 1001
    text = (
        "calc_time,funding_interval_hours,last_funding_rate\n"
        f"{first},8,0.0001\n"
        f"{second},8,0.0001\n"
    )
    payload = zipped("x.csv", text)
    with pytest.raises(MOD["CertificationError"]):
        MOD["validate_funding_archive"](payload, "BTCUSDT", "d" * 64)


def test_funding_header_change_fails_closed():
    text = (
        "funding_time,interval,rate\n"
        "1609459200000,8,0.0001\n"
    )
    payload = zipped("x.csv", text)
    with pytest.raises(MOD["CertificationError"]):
        MOD["validate_funding_archive"](payload, "BTCUSDT", "e" * 64)


def test_canonical_output_excludes_private_runtime_fields():
    rows = [{
        "symbol": "BTCUSDT",
        "market": "USD_M_FUTURES",
        "open_time": "2021-01-01T00:00:00.000Z",
        "_primary_epoch_us": 123,
    }]
    payload = MOD["canonical_output_rows"](rows)
    assert payload == (
        b'{"market":"USD_M_FUTURES","open_time":"2021-01-01T00:00:00.000Z","symbol":"BTCUSDT"}\n'
    )
