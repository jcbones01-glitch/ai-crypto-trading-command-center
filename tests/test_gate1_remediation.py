from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from research_core.archive_security import archive_member_symbol
from research_core.data_ingestion import parse_timestamp, verify_sha256_bytes
from research_core.historical_dataset import ingest_archives


# Gate 1 verification fixture tests are deterministic and contain no historical data.
def _row(dt: datetime, unit: str) -> str:
    scale = 1_000 if unit == "milliseconds" else 1_000_000
    stamp = int(dt.timestamp()) * scale
    return f"{stamp},100,105,99,103,12.5,0,0,0,0,0,0\n"


def _write_archive(path: Path, member_symbol: str, dt: datetime, unit: str) -> None:
    payload = _row(dt, unit).encode()
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr(f"{member_symbol}-1h-2021-01.csv", payload)


def test_archive_symbol_identity_is_derived_from_internal_member():
    assert archive_member_symbol("BTCUSDT-1h-2021-01.csv") == "BTCUSDT"
    assert archive_member_symbol("nested/ETHUSDT-1h-2021-01.csv") == "ETHUSDT"
    with pytest.raises(ValueError):
        archive_member_symbol("DOGEUSDT-1h-2021-01.csv")


def test_mismatched_internal_symbol_is_rejected(tmp_path: Path):
    archive = tmp_path / "BTCUSDT-1h-2021-01.zip"
    _write_archive(archive, "ETHUSDT", datetime(2021, 1, 1, tzinfo=timezone.utc), "milliseconds")
    with pytest.raises(ValueError, match="archive symbol mismatch"):
        ingest_archives([archive], "BTCUSDT")


def test_mismatched_archive_path_symbol_is_rejected(tmp_path: Path):
    archive = tmp_path / "ETHUSDT-1h-2021-01.zip"
    _write_archive(archive, "ETHUSDT", datetime(2021, 1, 1, tzinfo=timezone.utc), "milliseconds")
    with pytest.raises(ValueError, match="archive path symbol mismatch"):
        ingest_archives([archive], "BTCUSDT")


def test_malformed_zip_is_rejected(tmp_path: Path):
    archive = tmp_path / "BTCUSDT-1h-2021-01.zip"
    archive.write_bytes(b"not a zip")
    with pytest.raises(Exception):
        ingest_archives([archive], "BTCUSDT")


def test_binance_archive_boundaries_and_precision_transition(tmp_path: Path):
    first = tmp_path / "BTCUSDT-1h-2024-12.zip"
    second = tmp_path / "BTCUSDT-1h-2025-01.zip"
    _write_archive(first, "BTCUSDT", datetime(2024, 12, 31, 23, tzinfo=timezone.utc), "milliseconds")
    _write_archive(second, "BTCUSDT", datetime(2025, 1, 1, tzinfo=timezone.utc), "microseconds")
    dataset = ingest_archives([first, second], "BTCUSDT", expected_start=datetime(2024, 12, 31, 23, tzinfo=timezone.utc), expected_end=datetime(2025, 1, 1, 1, tzinfo=timezone.utc))
    assert dataset.metadata.timestamp_unit == "microseconds,milliseconds"
    assert dataset.bars[0].timestamp == datetime(2024, 12, 31, 23, tzinfo=timezone.utc)
    assert dataset.bars[-1].timestamp == datetime(2025, 1, 1, tzinfo=timezone.utc)


def test_timestamp_precision_is_runtime_deterministic():
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    millis, millis_unit = parse_timestamp(str(int(dt.timestamp() * 1_000)))
    micros, micros_unit = parse_timestamp(str(int(dt.timestamp() * 1_000_000)))
    assert millis == micros == dt
    assert millis_unit == "milliseconds"
    assert micros_unit == "microseconds"


def test_checksum_verification_accepts_valid_and_rejects_invalid():
    payload = b"fixture"
    import hashlib
    digest = hashlib.sha256(payload).hexdigest()
    assert verify_sha256_bytes(payload, f"{digest}  BTCUSDT-1h-2021-01.zip")
    assert not verify_sha256_bytes(payload, "0" * 64)


def test_archive_identity_and_dataset_identity_are_deterministic(tmp_path: Path):
    archive = tmp_path / "BTCUSDT-1h-2021-01.zip"
    _write_archive(archive, "BTCUSDT", datetime(2021, 1, 1, tzinfo=timezone.utc), "milliseconds")
    first = ingest_archives([archive], "BTCUSDT")
    second = ingest_archives([archive], "BTCUSDT")
    assert first.metadata.dataset_id == second.metadata.dataset_id
    assert first.metadata.source_identity == second.metadata.source_identity
    assert first.metadata.source_identity
