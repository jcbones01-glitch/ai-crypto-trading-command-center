from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import StringIO

import pytest

from research_core.data_ingestion import (
    NORMALIZATION_VERSION,
    archive_url,
    checksum_url,
    content_hash,
    dataset_identity,
    find_missing_intervals,
    make_metadata,
    normalize_csv,
    normalize_row,
    parse_timestamp,
    validate_dataset,
    verify_sha256_bytes,
)


def ts(dt: datetime, unit: str = "milliseconds") -> str:
    seconds = int(dt.timestamp())
    return str(seconds * (1_000 if unit == "milliseconds" else 1_000_000))


def row(dt: datetime, symbol="BTCUSDT", unit="milliseconds"):
    return [ts(dt, unit), "100.0", "105.0", "99.0", "103.0", "12.5", str(int(dt.timestamp() * 1000) + 3599999), "1287.5", "10", "6.0", "618.0", "0"]


def test_known_source_row_normalizes_exactly():
    bar, raw = normalize_row(row(datetime(2021, 1, 1, tzinfo=timezone.utc)), "BTCUSDT")
    assert bar.timestamp == datetime(2021, 1, 1, tzinfo=timezone.utc)
    assert bar.symbol == "BTC/USDT"
    assert bar.open == Decimal("100.0")
    assert bar.high == Decimal("105.0")
    assert bar.low == Decimal("99.0")
    assert bar.close == Decimal("103.0")
    assert bar.volume == Decimal("12.5")
    assert raw.timestamp_unit == "milliseconds"


def test_eth_symbol_normalizes():
    bar, _ = normalize_row(row(datetime(2021, 1, 1, tzinfo=timezone.utc)), "ETHUSDT")
    assert bar.symbol == "ETH/USDT"


def test_microseconds_are_detected():
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    parsed, unit = parse_timestamp(ts(dt, "microseconds"))
    assert parsed == dt
    assert unit == "microseconds"


def test_timestamp_precision_must_be_unambiguous():
    with pytest.raises(ValueError):
        parse_timestamp("12345")


def test_invalid_symbol_and_missing_field_rejected():
    with pytest.raises(ValueError):
        normalize_row(row(datetime(2021, 1, 1, tzinfo=timezone.utc)), "DOGEUSDT")
    with pytest.raises(ValueError):
        normalize_row(row(datetime(2021, 1, 1, tzinfo=timezone.utc))[:5], "BTCUSDT")


def test_invalid_decimal_and_financial_values_rejected():
    bad = row(datetime(2021, 1, 1, tzinfo=timezone.utc))
    bad[1] = "not-a-number"
    with pytest.raises(ValueError):
        normalize_row(bad, "BTCUSDT")
    bad = row(datetime(2021, 1, 1, tzinfo=timezone.utc))
    bad[3] = "110"
    with pytest.raises(ValueError):
        normalize_row(bad, "BTCUSDT")
    bad = row(datetime(2021, 1, 1, tzinfo=timezone.utc))
    bad[5] = "-1"
    with pytest.raises(ValueError):
        normalize_row(bad, "BTCUSDT")


def test_duplicate_and_out_of_order_are_rejected():
    base = datetime(2021, 1, 1, tzinfo=timezone.utc)
    duplicate = StringIO("\n".join(",".join(row(base)) for _ in range(2)))
    with pytest.raises(ValueError):
        normalize_csv(duplicate, "BTCUSDT")
    out_of_order = StringIO(",".join(row(base + timedelta(hours=1))) + "\n" + ",".join(row(base)))
    with pytest.raises(ValueError):
        normalize_csv(out_of_order, "BTCUSDT")


def test_missing_intervals_are_explicit_quality_events():
    base = datetime(2021, 1, 1, tzinfo=timezone.utc)
    data, unit = normalize_csv(StringIO(",".join(row(base)) + "\n" + ",".join(row(base + timedelta(hours=2)))), "BTCUSDT")
    report = validate_dataset(data, "BTCUSDT", unit)
    assert not report.valid
    assert [i.timestamp for i in report.issues if i.code == "missing_interval"] == [base + timedelta(hours=1)]


def test_archive_and_checksum_urls():
    url = archive_url("BTCUSDT", 2021, 1)
    assert url.endswith("BTCUSDT-1h-2021-01.zip")
    assert checksum_url(url).endswith(".zip.CHECKSUM")


def test_checksum_verification():
    payload = b"TEST FIXTURE ONLY"
    import hashlib
    digest = hashlib.sha256(payload).hexdigest()
    assert verify_sha256_bytes(payload, digest + "  archive.zip")
    assert not verify_sha256_bytes(payload, "0" * 64)
    with pytest.raises(ValueError):
        verify_sha256_bytes(payload, "bad")


def test_dataset_identity_is_deterministic_and_versioned():
    base = datetime(2021, 1, 1, tzinfo=timezone.utc)
    data, unit = normalize_csv(StringIO(",".join(row(base)) + "\n" + ",".join(row(base + timedelta(hours=1)))), "BTCUSDT")
    assert content_hash(data) == content_hash(data)
    assert dataset_identity(data) == dataset_identity(data)
    assert dataset_identity(data, NORMALIZATION_VERSION) != dataset_identity(data, "gate1-other-version")
    changed, _ = normalize_row(row(base + timedelta(hours=2)), "BTCUSDT")
    assert dataset_identity(data) != dataset_identity([*data, changed])
    metadata = make_metadata(data, "BTCUSDT", unit, source_identity="abc123")
    assert metadata.dataset_id == dataset_identity(data)
    assert metadata.content_hash == content_hash(data)
    assert metadata.source_identity == "abc123"
