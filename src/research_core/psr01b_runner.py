"""Frozen PSR-01B end-to-end orchestration.

The numerical/statistical components live in the neighboring psr01b_* modules.
This module fixes their execution order, fold/arm indexing, source-normalization
sequence, segment ordering, benchmark construction, bootstrap ordering, forecast
identity, and machine-readable result assembly.

Nothing in this module authorizes empirical execution.  The empirical source
entry point requires an explicit caller authorization boolean and must only be
invoked later by a separately reviewed governance/claim gate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

import numpy as np

from .ams_dep_treatment_aware_normalization_v2 import normalize_development_archives
from .data_interfaces import MarketBar
from .data_quality import scan_archive
from .data_quality_treatment_v2 import build_manifest
from .psr01b_benchmarks import buy_and_hold_segments, momentum_24h_segments
from .psr01b_core import (
    ARM_ORDER,
    PSR01BError,
    classify_success,
    evaluate_strategy_segments,
    forecast_vector_sha256,
    paired_segment_bootstrap,
    performance_metrics,
)
from .psr01b_egarch import select_best_order
from .psr01b_features import (
    ArmBars,
    compute_base_ohlcv_features,
    construct_missing_data_arm,
    warmup_start,
)
from .psr01b_matrix import (
    assemble_deployed_matrix,
    build_egarch_features,
    eligible_split_rows,
)
from .psr01b_model import final_refit_and_forecast, tune_fold
from .psr01b_preflight import (
    ROOT,
    load_registration,
    verify_archive_digest_metadata,
    verify_archive_inventory,
    verify_pre_source_read_contract,
    verify_runtime_versions,
    verify_thread_environment,
    verify_timestamp_boundary_metadata,
)
from .psr01b_ta import compute_ta_candidates, select_four_block_features


UTC = timezone.utc
SOURCE_START = datetime(2017, 12, 1, tzinfo=UTC)
SOURCE_END = datetime(2022, 1, 1, tzinfo=UTC)
PRIMARY_BLOCK_HOURS = 168
ROBUSTNESS_BLOCK_HOURS = (24, 72)
ARM_INDEX = {"PAPER_FILL": 0, "PROJECT_GAP_PRESERVING": 1}
FREEZE_PATH = ROOT / "research/governance/psr01b_implementation_freeze_v1.json"
APPROVED_SPEC_HEAD = "16d5193f0c80b5899f5084e76a42917e824e0936"
APPROVED_SPEC_BLOB_SHA1 = "47c5379eeb4eae8c5890814c92e29b86bfddb23e"
EXECUTION_ID = "PSR01B_REGISTERED_ONE_SHOT_V1"
EXPECTED_FOLD_ROWS = (
    (1, "2018-01-01T00:00:00Z", "2019-01-01T00:00:00Z", "2019-04-01T00:00:00Z", "2019-07-01T00:00:00Z"),
    (2, "2018-04-01T00:00:00Z", "2019-04-01T00:00:00Z", "2019-07-01T00:00:00Z", "2019-10-01T00:00:00Z"),
    (3, "2018-07-01T00:00:00Z", "2019-07-01T00:00:00Z", "2019-10-01T00:00:00Z", "2020-01-01T00:00:00Z"),
    (4, "2018-10-01T00:00:00Z", "2019-10-01T00:00:00Z", "2020-01-01T00:00:00Z", "2020-04-01T00:00:00Z"),
    (5, "2019-01-01T00:00:00Z", "2020-01-01T00:00:00Z", "2020-04-01T00:00:00Z", "2020-07-01T00:00:00Z"),
    (6, "2019-04-01T00:00:00Z", "2020-04-01T00:00:00Z", "2020-07-01T00:00:00Z", "2020-10-01T00:00:00Z"),
    (7, "2019-07-01T00:00:00Z", "2020-07-01T00:00:00Z", "2020-10-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    (8, "2019-10-01T00:00:00Z", "2020-10-01T00:00:00Z", "2021-01-01T00:00:00Z", "2021-04-01T00:00:00Z"),
    (9, "2020-01-01T00:00:00Z", "2021-01-01T00:00:00Z", "2021-04-01T00:00:00Z", "2021-07-01T00:00:00Z"),
    (10, "2020-04-01T00:00:00Z", "2021-04-01T00:00:00Z", "2021-07-01T00:00:00Z", "2021-10-01T00:00:00Z"),
    (11, "2020-07-01T00:00:00Z", "2021-07-01T00:00:00Z", "2021-10-01T00:00:00Z", "2022-01-01T00:00:00Z"),
)


@dataclass(frozen=True)
class FoldExecution:
    arm: str
    fold_number: int
    fold_index: int
    forecast_sha256: str
    forecast_count: int
    selected_features: tuple[str, ...]
    egarch_order: tuple[int, int, int]
    egarch_aic: float
    selected_trial_index: int
    final_model_seed: int
    baseline_segments: tuple[np.ndarray, ...]
    cost_aware_segments: tuple[np.ndarray, ...]
    buy_hold_segments: tuple[np.ndarray, ...]
    momentum_segments: tuple[np.ndarray, ...]
    baseline_turnover: float
    cost_aware_turnover: float
    baseline_completed_trades: int
    cost_aware_completed_trades: int

    def record(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "fold": self.fold_number,
            "fold_index": self.fold_index,
            "forecast_sha256": self.forecast_sha256,
            "forecast_count": self.forecast_count,
            "selected_features": list(self.selected_features),
            "egarch_order": list(self.egarch_order),
            "egarch_aic": self.egarch_aic,
            "selected_trial_index": self.selected_trial_index,
            "final_model_seed": self.final_model_seed,
            "fold_metrics": {
                "BASELINE_SIGN": _fold_metric_record(self.baseline_segments),
                "COST_AWARE": _fold_metric_record(self.cost_aware_segments),
                "BUY_AND_HOLD": _fold_metric_record(self.buy_hold_segments),
                "MOMENTUM_24H": _fold_metric_record(self.momentum_segments),
            },
        }


def _parse_utc(value: str) -> datetime:
    out = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if out.tzinfo is None or out.utcoffset() != timedelta(0):
        raise PSR01BError("registered fold boundary must be UTC")
    out = out.astimezone(UTC)
    if out.minute or out.second or out.microsecond:
        raise PSR01BError("registered fold boundary must be exact UTC hour")
    return out


def _registered_folds(registration: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    raw = registration.get("folds")
    if not isinstance(raw, list) or len(raw) != 11:
        raise PSR01BError("PSR-01B must contain exactly 11 registered folds")
    observed_rows = tuple(
        (
            int(item.get("fold", -1)),
            item.get("train_start"),
            item.get("train_end_validation_start"),
            item.get("validation_end_test_start"),
            item.get("test_end"),
        )
        for item in raw
    )
    if observed_rows != EXPECTED_FOLD_ROWS:
        raise PSR01BError("registered PSR-01B fold dates/order drift")

    out: list[dict[str, Any]] = []
    for expected_number, item in enumerate(raw, start=1):
        if int(item.get("fold", -1)) != expected_number:
            raise PSR01BError("PSR-01B fold numbering/order drift")
        train_start = _parse_utc(item["train_start"])
        validation_start = _parse_utc(item["train_end_validation_start"])
        test_start = _parse_utc(item["validation_end_test_start"])
        test_end = _parse_utc(item["test_end"])
        if not train_start < validation_start < test_start < test_end:
            raise PSR01BError("invalid registered fold chronology")
        out.append(
            {
                "fold": expected_number,
                "fold_index": expected_number - 1,
                "train_start": train_start,
                "validation_start": validation_start,
                "test_start": test_start,
                "test_end": test_end,
            }
        )
    return tuple(out)


def _git_blob_sha1(path: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "hash-object", "--", path],
            cwd=ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PSR01BError(f"cannot compute Git blob identity: {path}") from exc


def _git_head_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PSR01BError("cannot determine execution checkout HEAD") from exc


def load_implementation_freeze(path: Path = FREEZE_PATH) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PSR01BError("cannot load PSR-01B implementation freeze") from exc
    if data.get("freeze_id") != "PSR01B-IMPLEMENTATION-FREEZE-V1":
        raise PSR01BError("unexpected PSR-01B implementation freeze identity")
    return data


def verify_frozen_execution_identity(
    *,
    runner_label: str,
    freeze: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Verify the exact frozen one-shot execution identity before source bytes."""
    registration = load_registration()
    folds = _registered_folds(registration)
    frozen = dict(load_implementation_freeze() if freeze is None else freeze)

    approved = frozen.get("approved_specification") or {}
    expected_approved = {
        "issue": 90,
        "approval_decision": "APPROVE_PSR01B_BOUNDED_SPEC_FOR_IMPLEMENTATION",
        "approval_comment_id": 5821484000,
        "exact_approved_head": APPROVED_SPEC_HEAD,
        "specification_path": "research/governance/psr01b_bounded_spec_v1.json",
        "specification_git_blob_sha1": APPROVED_SPEC_BLOB_SHA1,
        "revision": 4,
    }
    if approved != expected_approved:
        raise PSR01BError("approved revision-4 specification identity drift")
    observed_spec_blob = _git_blob_sha1(approved["specification_path"])
    if observed_spec_blob != APPROVED_SPEC_BLOB_SHA1:
        raise PSR01BError("approved revision-4 specification blob mismatch")

    implementation = frozen.get("implementation") or {}
    candidate = implementation.get("implementation_candidate_commit")
    reviewed = implementation.get("reviewed_implementation_commit")
    if not isinstance(candidate, str) or len(candidate) != 40:
        raise PSR01BError("frozen implementation candidate identity missing")
    if implementation.get("independent_implementation_reviewed") is not True:
        raise PSR01BError("independent implementation review is not approved")
    if reviewed != candidate:
        raise PSR01BError("reviewed implementation identity does not equal frozen candidate")

    expected_implementation_blobs = frozen.get("implementation_file_git_blob_sha1") or {}
    if not expected_implementation_blobs:
        raise PSR01BError("frozen implementation blob inventory missing")
    observed_implementation_blobs = {
        str(path): _git_blob_sha1(str(path))
        for path in expected_implementation_blobs
    }
    if observed_implementation_blobs != expected_implementation_blobs:
        raise PSR01BError("frozen PSR-01B implementation blob mismatch")

    row_contract = registration["source"]["row_treatment_contract"]
    expected_upstream_blobs = frozen.get("pinned_upstream_git_blob_sha1") or {}
    if expected_upstream_blobs != row_contract["required_blob_sha1"]:
        raise PSR01BError("freeze/upstream normalization blob contract mismatch")
    observed_upstream_blobs = {
        str(path): _git_blob_sha1(str(path))
        for path in expected_upstream_blobs
    }
    observed_upstream_registration = _git_blob_sha1(
        row_contract["upstream_registration_path"]
    )
    verify_pre_source_read_contract(
        observed_upstream_blobs,
        observed_upstream_registration,
        registration,
    )

    runtime = verify_runtime_versions(runner_label=runner_label)
    thread_env = verify_thread_environment(environ)
    future = frozen.get("future_governance") or {}
    for flag in (
        "reviewed_candidate_anchor_created",
        "execution_authorized",
        "manual_confirmation_created",
        "one_shot_claim_created",
    ):
        if future.get(flag) is not True:
            raise PSR01BError(f"PSR-01B governance gate not satisfied: {flag}")

    freeze_blob = None
    if freeze is None:
        freeze_blob = _git_blob_sha1(
            str(FREEZE_PATH.relative_to(ROOT)).replace("\\", "/")
        )

    return {
        "execution_identity": EXECUTION_ID,
        "registration_id": registration["registration_id"],
        "registration_revision": int(registration["revision"]),
        "approved_specification_head": APPROVED_SPEC_HEAD,
        "approved_specification_git_blob_sha1": observed_spec_blob,
        "implementation_candidate_commit": candidate,
        "reviewed_implementation_commit": reviewed,
        "execution_checkout_head": _git_head_sha(),
        "implementation_freeze_git_blob_sha1": freeze_blob,
        "observed_implementation_file_git_blob_sha1": observed_implementation_blobs,
        "observed_upstream_git_blob_sha1": observed_upstream_blobs,
        "upstream_registration_path": row_contract["upstream_registration_path"],
        "observed_upstream_registration_git_blob_sha1": observed_upstream_registration,
        "runtime_versions": runtime,
        "thread_environment": thread_env,
        "registered_folds": [
            {
                "fold": int(fold["fold"]),
                "train_start": fold["train_start"].isoformat().replace("+00:00", "Z"),
                "validation_start": fold["validation_start"].isoformat().replace("+00:00", "Z"),
                "test_start": fold["test_start"].isoformat().replace("+00:00", "Z"),
                "test_end": fold["test_end"].isoformat().replace("+00:00", "Z"),
            }
            for fold in folds
        ],
        "governance": {
            "independent_implementation_reviewed": True,
            "reviewed_candidate_anchor_created": True,
            "execution_authorized": True,
            "manual_confirmation_created": True,
            "one_shot_claim_created": True,
        },
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_registered_source(*args, **kwargs):
    """Direct empirical normalization is disabled; use execute_registered_one_shot."""
    raise PSR01BError(
        "direct PSR-01B source normalization is disabled; use registered one-shot entry"
    )


def _normalize_registered_source(
    archive_paths: Sequence[Path],
    *,
    runner_label: str,
    evidence_out: dict[str, Any] | None = None,
) -> tuple[MarketBar, ...]:
    """Internal source-normalization stage for the identity-locked one-shot path."""
    registration = load_registration()
    verify_runtime_versions(runner_label=runner_label)

    row_contract = registration["source"]["row_treatment_contract"]
    observed_import_blobs = {
        path: _git_blob_sha1(path)
        for path in row_contract["required_blob_sha1"]
    }
    observed_upstream = _git_blob_sha1(row_contract["upstream_registration_path"])

    # This complete identity/boundary gate must finish before opening archive
    # bytes, including before the SHA-256 pass.
    verify_pre_source_read_contract(
        observed_import_blobs,
        observed_upstream,
        registration,
    )

    ordered_paths = tuple(sorted((Path(p) for p in archive_paths), key=lambda p: p.name))
    verify_archive_inventory([p.name for p in ordered_paths], registration)

    # Revision-4 requires byte hashes before scanner use.
    observed_sha256 = {path.name: _sha256_file(path) for path in ordered_paths}
    verify_archive_digest_metadata(observed_sha256, registration)

    reports = [
        scan_archive(path, "BTCUSDT", checksum_verified=True)
        for path in ordered_paths
    ]
    manifest = build_manifest(
        "BTCUSDT",
        reports,
        research_start=SOURCE_START,
        research_end=SOURCE_END,
    )
    normalized = normalize_development_archives(
        "BTCUSDT",
        ordered_paths,
        reports,
        manifest,
    )
    bars = tuple(
        bar
        for bar in normalized.bars
        if SOURCE_START <= bar.timestamp.astimezone(UTC) < SOURCE_END
    )
    if not bars:
        raise PSR01BError("PSR-01B source normalization produced no registered rows")
    verify_timestamp_boundary_metadata(
        [int(bar.timestamp.astimezone(UTC).timestamp()) for bar in bars],
        registration,
    )
    if evidence_out is not None:
        evidence_out.clear()
        evidence_out.update(
            {
                "archive_sha256": dict(observed_sha256),
                "normalized_row_count": len(bars),
                "first_timestamp": bars[0].timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                "last_timestamp": bars[-1].timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            }
        )
    return bars


def _training_return_segments(
    arm: ArmBars,
    *,
    train_start: datetime,
    train_end: datetime,
) -> tuple[np.ndarray, ...]:
    """Return y_t=100*log(C_t/C_t-1) with endpoint label inside training."""
    segments: list[list[float]] = []
    current: list[float] = []
    for i in range(1, len(arm.bars)):
        previous = arm.bars[i - 1]
        bar = arm.bars[i]
        stamp = bar.timestamp.astimezone(UTC)
        if not (train_start <= stamp < train_end):
            if current and stamp >= train_end:
                segments.append(current)
                current = []
            continue
        contiguous = (
            arm.segment_ids[i] == arm.segment_ids[i - 1]
            and arm.segment_indices[i] == arm.segment_indices[i - 1] + 1
            and stamp - previous.timestamp.astimezone(UTC) == timedelta(hours=1)
        )
        if not contiguous:
            if current:
                segments.append(current)
                current = []
            continue
        value = 100.0 * math.log(float(bar.close) / float(previous.close))
        if not np.isfinite(value):
            raise PSR01BError("nonfinite EGARCH training return")
        current.append(float(value))
    if current:
        segments.append(current)
    if not segments or any(len(segment) == 0 for segment in segments):
        raise PSR01BError("no eligible EGARCH training return segments")
    return tuple(np.asarray(segment, dtype=np.float64) for segment in segments)


def _split_test_segments(arm: ArmBars, test_rows) -> tuple[np.ndarray, ...]:
    indices = np.asarray(test_rows.indices, dtype=np.int64)
    if indices.ndim != 1 or len(indices) == 0:
        raise PSR01BError("test split must contain eligible rows")
    groups: list[list[int]] = [[int(indices[0])]]
    for raw in indices[1:]:
        i = int(raw)
        previous = groups[-1][-1]
        same_contiguous_segment = (
            i == previous + 1
            and arm.segment_ids[i] == arm.segment_ids[previous]
            and arm.bars[i].timestamp - arm.bars[previous].timestamp == timedelta(hours=1)
        )
        if same_contiguous_segment:
            groups[-1].append(i)
        else:
            groups.append([i])
    return tuple(np.asarray(group, dtype=np.int64) for group in groups)


def _aligned_segments(
    values: Sequence[float],
    test_rows,
    test_groups: Sequence[np.ndarray],
) -> tuple[np.ndarray, ...]:
    values_arr = np.asarray(values, dtype=np.float64)
    if values_arr.shape != (len(test_rows.indices),):
        raise PSR01BError("test value vector does not align with eligible origins")
    position_by_index = {int(index): pos for pos, index in enumerate(test_rows.indices)}
    segments = []
    for group in test_groups:
        positions = [position_by_index[int(index)] for index in group]
        segment = values_arr[np.asarray(positions, dtype=np.int64)]
        if not np.isfinite(segment).all():
            raise PSR01BError("nonfinite segmented test value")
        segments.append(segment)
    return tuple(segments)


def _momentum_24h_values(arm: ArmBars, test_rows) -> np.ndarray:
    values = np.zeros(len(test_rows.indices), dtype=np.float64)
    for pos, raw_index in enumerate(test_rows.indices):
        i = int(raw_index)
        if i < 24:
            values[pos] = 0.0
            continue
        same_segment = (
            arm.segment_ids[i] == arm.segment_ids[i - 24]
            and arm.segment_indices[i] - arm.segment_indices[i - 24] == 24
            and arm.bars[i].timestamp - arm.bars[i - 24].timestamp == timedelta(hours=24)
        )
        if not same_segment:
            values[pos] = 0.0
            continue
        values[pos] = math.log(float(arm.bars[i].close) / float(arm.bars[i - 24].close))
    if not np.isfinite(values).all():
        raise PSR01BError("nonfinite momentum benchmark signal")
    return values


def _evaluate_rule_by_segment(
    forecast_segments: Sequence[Sequence[float]],
    realized_segments: Sequence[Sequence[float]],
    *,
    rule: str,
) -> tuple[tuple[np.ndarray, ...], float, int]:
    returns: list[np.ndarray] = []
    turnover = 0.0
    completed = 0
    for forecast, realized in zip(forecast_segments, realized_segments):
        result = evaluate_strategy_segments([forecast], [realized], rule=rule)
        returns.append(np.asarray(result.returns, dtype=np.float64))
        turnover += result.turnover
        completed += result.completed_trades
    return tuple(returns), float(turnover), int(completed)


def _benchmark_by_segment(
    realized_segments: Sequence[Sequence[float]],
    momentum_segments: Sequence[Sequence[float]],
) -> tuple[tuple[np.ndarray, ...], tuple[np.ndarray, ...]]:
    buy: list[np.ndarray] = []
    momentum: list[np.ndarray] = []
    for realized, signal in zip(realized_segments, momentum_segments):
        buy.append(np.asarray(buy_and_hold_segments([realized]).returns, dtype=np.float64))
        momentum.append(
            np.asarray(momentum_24h_segments([signal], [realized]).returns, dtype=np.float64)
        )
    return tuple(buy), tuple(momentum)


def _run_arm_fold(
    normalized_bars: Sequence[MarketBar],
    *,
    arm_name: str,
    fold: Mapping[str, Any],
) -> FoldExecution:
    fold_number = int(fold["fold"])
    fold_index = int(fold["fold_index"])
    train_start = fold["train_start"]
    validation_start = fold["validation_start"]
    test_start = fold["test_start"]
    test_end = fold["test_end"]

    arm = construct_missing_data_arm(
        normalized_bars,
        arm=arm_name,
        interval_start=warmup_start(train_start),
        interval_end_exclusive=test_end,
    )
    base = compute_base_ohlcv_features(arm)
    candidates = compute_ta_candidates(arm)
    selection_features = select_four_block_features(
        arm,
        candidates,
        train_start=train_start,
        train_end=validation_start,
    )

    training_segments = _training_return_segments(
        arm,
        train_start=train_start,
        train_end=validation_start,
    )
    egarch_fit = select_best_order(training_segments)
    if egarch_fit.params is None or egarch_fit.aic is None:
        raise PSR01BError("selected EGARCH order has no usable fitted state")
    egarch = build_egarch_features(
        arm,
        replay_start=train_start,
        params=egarch_fit.params,
        order=egarch_fit.order,
    )
    deployed = assemble_deployed_matrix(
        base=base,
        selection=selection_features,
        egarch=egarch,
    )

    train_rows = eligible_split_rows(
        arm,
        deployed,
        candidates.target_next_hour,
        split_start=train_start,
        split_end=validation_start,
    )
    validation_rows = eligible_split_rows(
        arm,
        deployed,
        candidates.target_next_hour,
        split_start=validation_start,
        split_end=test_start,
    )
    test_rows = eligible_split_rows(
        arm,
        deployed,
        candidates.target_next_hour,
        split_start=test_start,
        split_end=test_end,
    )

    model_selection = tune_fold(
        X_train=train_rows.X,
        y_train_raw=train_rows.y,
        X_validation=validation_rows.X,
        y_validation_raw=validation_rows.y,
        arm=arm_name,
        fold_index=fold_index,
    )
    forecast = final_refit_and_forecast(
        X_train_eligible=train_rows.X,
        y_train_raw_eligible=train_rows.y,
        X_validation_eligible=validation_rows.X,
        y_validation_raw_eligible=validation_rows.y,
        X_test=test_rows.X,
        selection=model_selection,
    )

    if len(forecast.forecasts_raw) != len(test_rows.origin_timestamps):
        raise PSR01BError("forecast vector/test-origin length mismatch")
    timestamps = [
        int(stamp.astimezone(UTC).timestamp())
        for stamp in test_rows.origin_timestamps
    ]
    forecast_hash = forecast_vector_sha256(timestamps, forecast.forecasts_raw)

    test_groups = _split_test_segments(arm, test_rows)
    forecast_segments = _aligned_segments(forecast.forecasts_raw, test_rows, test_groups)
    realized_segments = _aligned_segments(test_rows.y, test_rows, test_groups)

    baseline_segments, baseline_turnover, baseline_completed = _evaluate_rule_by_segment(
        forecast_segments,
        realized_segments,
        rule="BASELINE_SIGN",
    )
    cost_segments, cost_turnover, cost_completed = _evaluate_rule_by_segment(
        forecast_segments,
        realized_segments,
        rule="COST_AWARE",
    )

    momentum_values = _momentum_24h_values(arm, test_rows)
    momentum_segments = _aligned_segments(momentum_values, test_rows, test_groups)
    buy_segments, momentum_return_segments = _benchmark_by_segment(
        realized_segments,
        momentum_segments,
    )

    return FoldExecution(
        arm=arm_name,
        fold_number=fold_number,
        fold_index=fold_index,
        forecast_sha256=forecast_hash,
        forecast_count=len(timestamps),
        selected_features=tuple(selection_features.selected_names),
        egarch_order=tuple(egarch_fit.order),
        egarch_aic=float(egarch_fit.aic),
        selected_trial_index=int(model_selection.selected.trial_number),
        final_model_seed=int(forecast.random_state),
        baseline_segments=baseline_segments,
        cost_aware_segments=cost_segments,
        buy_hold_segments=buy_segments,
        momentum_segments=momentum_return_segments,
        baseline_turnover=baseline_turnover,
        cost_aware_turnover=cost_turnover,
        baseline_completed_trades=baseline_completed,
        cost_aware_completed_trades=cost_completed,
    )


def _concat_segments(segments: Sequence[np.ndarray]) -> np.ndarray:
    if not segments:
        raise PSR01BError("no evaluation segments")
    return np.concatenate([np.asarray(segment, dtype=np.float64) for segment in segments])


def _fold_metric_record(segments: Sequence[np.ndarray]) -> dict[str, Any]:
    metrics = performance_metrics(_concat_segments(segments))
    total_return = float(metrics["total_return"])
    arc = float(metrics["ARC"])
    if not np.isfinite(total_return) or not np.isfinite(arc):
        raise PSR01BError("nonfinite registered fold return metric")
    asd_raw = metrics["ASD"]
    sharpe_raw = metrics["SHARPE"]
    asd = None
    if asd_raw is not None and np.isfinite(float(asd_raw)):
        asd = float(asd_raw)
    sharpe = None
    if sharpe_raw is not None and np.isfinite(float(sharpe_raw)):
        sharpe = float(sharpe_raw)
    return {
        "N": int(metrics["N"]),
        "fold_total_return": total_return,
        "fold_ARC": arc,
        "fold_ASD": asd,
        "fold_SHARPE": sharpe,
    }


def _bootstrap_record(result) -> dict[str, Any]:
    return asdict(result)


def run_from_normalized_bars(
    normalized_bars: Sequence[MarketBar],
) -> dict[str, Any]:
    """Run the complete registered PSR-01B experiment from normalized bars.

    This function contains no source acquisition.  It is the result-affecting
    orchestration path exercised synthetically before any empirical source gate.
    """
    reg = load_registration()
    folds = _registered_folds(reg)
    bars = tuple(normalized_bars)
    if not bars:
        raise PSR01BError("normalized PSR-01B source rows are empty")

    fold_runs_by_arm: dict[str, list[FoldExecution]] = {arm: [] for arm in ARM_ORDER}
    # Fixed execution order: registered arm order, then registered fold order.
    for arm in ARM_ORDER:
        for fold in folds:
            fold_runs_by_arm[arm].append(
                _run_arm_fold(
                    bars,
                    arm_name=arm,
                    fold=fold,
                )
            )

    arm_records: dict[str, Any] = {}
    summaries: dict[str, dict[str, float | int | None]] = {}

    # Fixed inference order per arm: primary 168h, then diagnostics 24h and 72h.
    for arm in ARM_ORDER:
        runs = fold_runs_by_arm[arm]
        baseline_segments = tuple(
            segment for run in runs for segment in run.baseline_segments
        )
        cost_segments = tuple(
            segment for run in runs for segment in run.cost_aware_segments
        )
        buy_segments = tuple(
            segment for run in runs for segment in run.buy_hold_segments
        )
        momentum_segments = tuple(
            segment for run in runs for segment in run.momentum_segments
        )

        primary = paired_segment_bootstrap(
            baseline_segments,
            cost_segments,
            block_hours=PRIMARY_BLOCK_HOURS,
            arm_index=ARM_INDEX[arm],
        )
        diagnostics = {
            str(block): paired_segment_bootstrap(
                baseline_segments,
                cost_segments,
                block_hours=block,
                arm_index=ARM_INDEX[arm],
            )
            for block in ROBUSTNESS_BLOCK_HOURS
        }

        baseline_metrics = performance_metrics(_concat_segments(baseline_segments))
        cost_metrics = performance_metrics(_concat_segments(cost_segments))
        buy_metrics = performance_metrics(_concat_segments(buy_segments))
        momentum_metrics = performance_metrics(_concat_segments(momentum_segments))

        summary: dict[str, float | int | None] = {
            "all_record_mean": primary.all_record_mean,
            "inference_universe_mean": primary.inference_universe_mean,
            "eligible_primary_segments": primary.eligible_segments,
            "primary_p_value": primary.p_value,
            "cost_aware_turnover": float(sum(run.cost_aware_turnover for run in runs)),
            "baseline_turnover": float(sum(run.baseline_turnover for run in runs)),
            "cost_aware_completed_trades": int(
                sum(run.cost_aware_completed_trades for run in runs)
            ),
            "cost_aware_sharpe": cost_metrics["SHARPE"],
            "baseline_sharpe": baseline_metrics["SHARPE"],
        }
        summaries[arm] = summary
        arm_records[arm] = {
            "folds": [run.record() for run in runs],
            "baseline_metrics": baseline_metrics,
            "cost_aware_metrics": cost_metrics,
            "buy_and_hold_metrics": buy_metrics,
            "momentum_24h_metrics": momentum_metrics,
            "baseline_turnover": summary["baseline_turnover"],
            "cost_aware_turnover": summary["cost_aware_turnover"],
            "baseline_completed_trades": int(
                sum(run.baseline_completed_trades for run in runs)
            ),
            "cost_aware_completed_trades": summary["cost_aware_completed_trades"],
            "primary_168h": _bootstrap_record(primary),
            "diagnostic_24h": _bootstrap_record(diagnostics["24"]),
            "diagnostic_72h": _bootstrap_record(diagnostics["72"]),
        }

    decision = classify_success(summaries)
    return {
        "registration_id": reg["registration_id"],
        "revision": int(reg["revision"]),
        "fold_index_base": 0,
        "trial_index_base": 0,
        "execution_order": {
            "arms": list(ARM_ORDER),
            "folds": [int(fold["fold"]) for fold in folds],
            "bootstrap_hours": [168, 24, 72],
        },
        "arms": arm_records,
        "success_token": decision,
    }


def execute_registered_one_shot(
    archive_paths: Sequence[Path],
    *,
    result_path: Path,
    runner_label: str,
    source_read_authorized: bool = False,
) -> dict[str, Any]:
    """Single identity-locked source -> experiment -> result-writing entry path.

    This function does not grant execution authority.  It remains inert unless
    a future reviewed governance state is present in the freeze and the caller
    also supplies the explicit source-read confirmation.
    """
    if source_read_authorized is not True:
        raise PSR01BError("PSR-01B empirical source read is not authorized")

    provenance = verify_frozen_execution_identity(runner_label=runner_label)
    source_evidence: dict[str, Any] = {}
    bars = _normalize_registered_source(
        archive_paths,
        runner_label=runner_label,
        evidence_out=source_evidence,
    )
    result = run_from_normalized_bars(bars)
    result["provenance"] = {
        **provenance,
        "source": source_evidence,
    }
    write_result_json(Path(result_path), result)
    return result


def write_result_json(path: Path, result: Mapping[str, Any]) -> None:
    """Write one deterministic machine-readable result record."""
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)
    Path(path).write_text(payload + "\n", encoding="utf-8")
