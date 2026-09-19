"""Build and certify ECO-DERIV-V1 from certified Development inputs only."""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import runpy
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zipfile import ZipFile

from research_core.data_ingestion import (
    archive_url as spot_archive_url,
    checksum_url,
    parse_timestamp,
    verify_sha256_bytes,
)
from research_core.data_quality import scan_archive
from research_core.data_quality_treatment_v2 import build_manifest
from research_core.market_ecology import (
    FundingPoint,
    FuturesPoint,
    SpotPoint,
    build_eco_deriv_rows,
    canonical_jsonl,
    feature_identity,
    iso_to_epoch_us,
)

ROOT = Path(__file__).resolve().parents[2]
FEATURE_SPEC = Path("docs/GATE2_CYCLE9_ECO_DERIV_V1_FEATURE_SPEC.md")
NUMERICAL = Path("docs/GATE2_CYCLE9_ECO_DERIV_V1_NUMERICAL_CONTRACT.md")
SPEC_COMMIT = "5c7a1aee91e0bc8d8a665c71b0ddc8b8f23952a8"

DERIV_CERTIFIER = Path("research/scripts/certify_cycle9_derivatives_development_v1.py")
DERIV_PROTOCOL = Path("docs/GATE2_CYCLE9_DERIVATIVES_DEVELOPMENT_CERTIFICATION_PROTOCOL_V1.md")
DERIV_CONTRACT = Path("docs/GATE2_CYCLE9_DERIVATIVES_NORMALIZATION_CONTRACT_V1.md")

START = datetime(2017, 8, 17, tzinfo=timezone.utc)
END = datetime(2022, 1, 1, tzinfo=timezone.utc)
DERIV_START = datetime(2020, 1, 1, tzinfo=timezone.utc)

EXPECTED_SPOT = {
    "BTCUSDT": "1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf",
    "ETHUSDT": "d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f",
}
EXPECTED_DERIV_COMBINED = "061c7b85e1fef9fcff1bc761f8c1198db9ae2a9e49277b8b0e80ab7ea2c56e11"
EXPECTED_DERIV_STREAMS = {
    "btcusdt_kline": "6ec4f168e97736d6a5481280e82eb0b56eb5a5247e113d2467e7f31d473b5ea0",
    "btcusdt_funding": "afa2f2a40031e4d4000c3e0f79f83f210d104e49b33876eaeb506a92b716aa08",
    "ethusdt_kline": "51c5accee0ae609be005fdeeb744dbfe64a6e5a7f35a3bb5cb96cc2439430745",
    "ethusdt_funding": "61ebc26000bee2452e15b79487a6fb6ec202e6a4e717a00f30c9bfd4a57759a2",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def months():
    year, month = START.year, START.month
    while (year, month) < (END.year, END.month):
        yield year, month
        month += 1
        if month == 13:
            year += 1
            month = 1


def fetch(url: str) -> bytes:
    last = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "ai-crypto-trading-command-center/1"})
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read()
        except Exception as exc:
            last = exc
            if attempt < 2:
                time.sleep((1, 2)[attempt])
    raise last


def in_break(ts: datetime, breaks) -> bool:
    for break_ in breaks:
        start = datetime.fromisoformat(break_.start)
        end = datetime.fromisoformat(break_.end)
        if start <= ts < end:
            return True
    return False


def parse_certified_spot(
    archive_path: Path,
    symbol: str,
    valid_timestamps: set[datetime],
    breaks,
) -> list[SpotPoint]:
    points = []
    with ZipFile(archive_path) as archive:
        members = [name for name in archive.namelist() if not name.endswith("/")]
        if len(members) != 1:
            raise RuntimeError("unexpected spot archive structure")
        text = archive.read(members[0]).decode("utf-8")
    for row in csv.reader(text.splitlines()):
        if not row or row[0].strip().lower() in {"open time", "timestamp"}:
            continue
        if len(row) < 5:
            continue
        try:
            ts, _ = parse_timestamp(row[0])
            if ts not in valid_timestamps or not (START <= ts < END) or in_break(ts, breaks):
                continue
            close = Decimal(row[4])
            if not close.is_finite() or close <= 0:
                raise RuntimeError("invalid certified spot close")
            epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
            delta = ts - epoch
            epoch_us = (
                delta.days * 86_400_000_000
                + delta.seconds * 1_000_000
                + delta.microseconds
            )
            points.append(SpotPoint(epoch_us, close))
        except (ValueError, InvalidOperation) as exc:
            raise RuntimeError(f"unexpected invalid row inside certified spot archive: {archive_path}") from exc
    return points


def load_certified_spot(symbol: str, root: Path) -> tuple[list[SpotPoint], dict]:
    scans = []
    paths = []
    for year, month in months():
        url = spot_archive_url(symbol, year, month)
        payload = fetch(url)
        checksum = fetch(checksum_url(url)).decode("utf-8")
        if not verify_sha256_bytes(payload, checksum):
            raise RuntimeError(f"spot checksum mismatch: {url}")
        path = root / symbol / Path(url).name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        scans.append(scan_archive(path, symbol, True))
        paths.append(path)

    manifest = build_manifest(symbol, scans, START, END)
    if manifest.dataset_identity != EXPECTED_SPOT[symbol]:
        raise RuntimeError(
            f"spot dataset identity mismatch for {symbol}: "
            f"{manifest.dataset_identity} != {EXPECTED_SPOT[symbol]}"
        )

    points = []
    for path, scan in zip(paths, scans):
        points.extend(
            parse_certified_spot(
                path, symbol, set(scan.valid_timestamps), manifest.continuity_breaks
            )
        )
    points.sort(key=lambda point: point.open_epoch_us)
    if any(a.open_epoch_us >= b.open_epoch_us for a, b in zip(points, points[1:])):
        raise RuntimeError("certified spot timestamps not unique/increasing")

    return points, {
        "dataset_identity": manifest.dataset_identity,
        "source_integrity": manifest.source_integrity,
        "research_certification": manifest.research_certification,
        "continuity_break_count": len(manifest.continuity_breaks),
        "usable_spot_point_count": len(points),
    }


def reproduce_derivatives():
    module = runpy.run_path(str(ROOT / DERIV_CERTIFIER))
    streams = [
        module["certify_stream"](kind, symbol)
        for symbol in ("BTCUSDT", "ETHUSDT")
        for kind in ("kline", "funding")
    ]
    if any(item["status"] != "PASS" for item in streams):
        raise RuntimeError("certified derivatives source no longer reproduces")

    for item in streams:
        expected = EXPECTED_DERIV_STREAMS[item["stream"]]
        if item["normalized_data_identity"] != expected:
            raise RuntimeError(
                f"derivatives stream identity mismatch: {item['stream']} "
                f"{item['normalized_data_identity']} != {expected}"
            )

    identities = {
        item["stream"]: {
            "source_manifest_identity": item["source_manifest_identity"],
            "normalized_data_identity": item["normalized_data_identity"],
        }
        for item in streams
    }
    combined = sha256_bytes(
        canonical_json_bytes(
            {
                "protocol_sha256": sha256_file(ROOT / DERIV_PROTOCOL),
                "normalization_contract_sha256": sha256_file(ROOT / DERIV_CONTRACT),
                "streams": identities,
            }
        )
    )
    if combined != EXPECTED_DERIV_COMBINED:
        raise RuntimeError(
            f"combined derivatives identity mismatch: {combined} != {EXPECTED_DERIV_COMBINED}"
        )

    by_stream = {}
    for item in streams:
        rows = [
            json.loads(line)
            for line in item["_normalized_bytes"].decode("utf-8").splitlines()
            if line
        ]
        by_stream[item["stream"]] = rows
    return combined, by_stream


def derivative_points(symbol: str, by_stream: dict):
    prefix = symbol.lower()
    futures_rows = by_stream[f"{prefix}_kline"]
    funding_rows = by_stream[f"{prefix}_funding"]

    futures = [
        FuturesPoint(
            iso_to_epoch_us(row["open_time"]),
            Decimal(row["close"]),
        )
        for row in futures_rows
    ]
    funding = [
        FundingPoint(
            iso_to_epoch_us(row["calc_time"]),
            Decimal(row["last_funding_rate"]),
            Decimal(row["funding_interval_hours"]),
            row["calc_time"],
        )
        for row in funding_rows
    ]
    return futures, funding


def provenance() -> dict:
    executing = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    for path in (FEATURE_SPEC, NUMERICAL):
        frozen = subprocess.check_output(
            ["git", "show", f"{SPEC_COMMIT}:{path.as_posix()}"],
            cwd=ROOT,
        )
        if frozen != (ROOT / path).read_bytes():
            raise RuntimeError(f"frozen ECO-DERIV specification changed: {path}")
    return {
        "executing_commit": executing,
        "checked_out_commit": executing,
        "specification_commit": SPEC_COMMIT,
        "feature_spec_sha256": sha256_file(ROOT / FEATURE_SPEC),
        "numerical_contract_sha256": sha256_file(ROOT / NUMERICAL),
    }


def main() -> None:
    meta = provenance()
    output = ROOT / "gate2_cycle9_eco_deriv_v1_results"
    output.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="eco-deriv-spot-") as td:
        spot_root = Path(td)
        spot = {}
        spot_meta = {}
        for symbol in ("BTCUSDT", "ETHUSDT"):
            spot[symbol], spot_meta[symbol] = load_certified_spot(symbol, spot_root)

        derivatives_identity, deriv_rows = reproduce_derivatives()

        assets = {}
        feature_ids = {}
        for symbol in ("BTCUSDT", "ETHUSDT"):
            futures, funding = derivative_points(symbol, deriv_rows)
            rows, diagnostics = build_eco_deriv_rows(
                symbol,
                spot[symbol],
                futures,
                funding,
                iso_to_epoch_us("2022-01-01T00:00:00.000Z"),
            )
            if not rows:
                raise RuntimeError(f"no complete ECO-DERIV rows for {symbol}")
            identity = feature_identity(rows)
            feature_ids[symbol] = identity
            payload = canonical_jsonl(rows)
            if sha256_bytes(payload) != identity:
                raise RuntimeError("feature identity/canonical payload mismatch")
            compressed = gzip.compress(payload, mtime=0)
            (output / f"{symbol.lower()}_eco_deriv_v1.jsonl.gz").write_bytes(compressed)
            assets[symbol] = {
                "spot_input": spot_meta[symbol],
                "derivatives_kline_identity": EXPECTED_DERIV_STREAMS[f"{symbol.lower()}_kline"],
                "derivatives_funding_identity": EXPECTED_DERIV_STREAMS[f"{symbol.lower()}_funding"],
                "diagnostics": diagnostics,
                "feature_identity": identity,
                "feature_jsonl_sha256": sha256_bytes(payload),
                "feature_gzip_sha256": sha256_bytes(compressed),
            }

    combined = sha256_bytes(
        canonical_json_bytes(
            {
                "derivatives_combined_dataset_identity": derivatives_identity,
                "feature_identities": feature_ids,
                "feature_spec_sha256": meta["feature_spec_sha256"],
                "spot_dataset_identities": EXPECTED_SPOT,
            }
        )
    )

    report = {
        "feature_version": "ECO-DERIV-V1",
        "classification": "CAUSAL_FEATURE_INFRASTRUCTURE_NOT_TRADING_EVIDENCE",
        "provenance": meta,
        "input_identities": {
            "spot": EXPECTED_SPOT,
            "derivatives_combined": derivatives_identity,
            "derivatives_streams": EXPECTED_DERIV_STREAMS,
        },
        "assets": assets,
        "combined_feature_identity": combined,
        "validation_or_oos_accessed": False,
        "forward_returns_calculated": False,
        "strategy_pnl_calculated": False,
        "strategy_signals_generated": False,
        "strategy_thresholds_searched": False,
        "status": "ECO_DERIV_V1_READY",
    }
    (output / "eco_deriv_v1_certification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print("ECO_DERIV_V1_READY")
    for symbol in ("BTCUSDT", "ETHUSDT"):
        diag = assets[symbol]["diagnostics"]
        print(
            symbol,
            diag["futures_candidate_hour_count"],
            diag["spot_futures_exact_timestamp_intersection_count"],
            diag["complete_feature_row_count"],
            diag["omitted_by_reason"],
            assets[symbol]["feature_identity"],
        )
    print("COMBINED_FEATURE_IDENTITY", combined)


if __name__ == "__main__":
    main()
