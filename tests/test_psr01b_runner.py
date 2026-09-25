"""Synthetic/offline integration tests for the frozen PSR-01B runner."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import numpy as np
import pytest

import research_core.psr01b_runner as runner
from research_core.data_interfaces import MarketBar
from research_core.psr01b_core import BootstrapResult, PSR01BError
from research_core.psr01b_features import ArmBars
from research_core.psr01b_matrix import SplitRows


UTC = timezone.utc


def _bar(stamp, price):
    value = Decimal(str(price))
    return MarketBar(
        timestamp=stamp,
        symbol="BTCUSDT",
        open=value,
        high=value,
        low=value,
        close=value,
        volume=Decimal("1"),
    )


def test_empirical_source_entry_point_is_inert_without_explicit_authorization(monkeypatch):
    touched = []

    def forbidden(*args, **kwargs):
        touched.append(True)
        raise AssertionError("source bytes must not be touched")

    monkeypatch.setattr(runner, "_sha256_file", forbidden)
    with pytest.raises(PSR01BError, match="not authorized"):
        runner.normalize_registered_source(
            [],
            runner_label="ubuntu-24.04",
            source_read_authorized=False,
        )
    assert touched == []


def test_registered_source_pipeline_order_is_frozen_without_real_empirical_reads(tmp_path, monkeypatch):
    reg = runner.load_registration()
    names = list(reg["source"]["archive_sha256"])
    paths = []
    for name in names:
        path = tmp_path / name
        path.write_bytes(b"synthetic-placeholder")
        paths.append(path)

    events = []
    row_contract = reg["source"]["row_treatment_contract"]

    monkeypatch.setattr(runner, "verify_runtime_versions", lambda **kwargs: events.append("runtime"))
    monkeypatch.setattr(
        runner,
        "_git_blob_sha1",
        lambda path: (
            row_contract["upstream_registration_blob_sha1"]
            if path == row_contract["upstream_registration_path"]
            else row_contract["required_blob_sha1"][path]
        ),
    )

    original_pre_source = runner.verify_pre_source_read_contract

    def pre_source(blobs, upstream, registration):
        events.append("pre_source")
        return original_pre_source(blobs, upstream, registration)

    monkeypatch.setattr(runner, "verify_pre_source_read_contract", pre_source)

    expected_hash = reg["source"]["archive_sha256"]

    def fake_sha(path):
        assert "pre_source" in events
        events.append(f"sha:{path.name}")
        return expected_hash[path.name]

    monkeypatch.setattr(runner, "_sha256_file", fake_sha)

    def fake_scan(path, symbol, checksum_verified=True):
        assert any(item.startswith("sha:") for item in events)
        assert symbol == "BTCUSDT"
        assert checksum_verified is True
        events.append(f"scan:{path.name}")
        return SimpleNamespace(archive=path.name)

    monkeypatch.setattr(runner, "scan_archive", fake_scan)

    def fake_manifest(symbol, reports, research_start, research_end):
        assert len(reports) == 49
        assert research_start == runner.SOURCE_START
        assert research_end == runner.SOURCE_END
        events.append("manifest")
        return object()

    monkeypatch.setattr(runner, "build_manifest", fake_manifest)

    bars = (
        _bar(datetime(2017, 12, 1, tzinfo=UTC), 100),
        _bar(datetime(2017, 12, 1, 1, tzinfo=UTC), 101),
    )

    def fake_normalize(symbol, ordered_paths, reports, manifest):
        assert symbol == "BTCUSDT"
        assert [p.name for p in ordered_paths] == sorted(names)
        events.append("normalize")
        return SimpleNamespace(bars=bars)

    monkeypatch.setattr(runner, "normalize_development_archives", fake_normalize)

    out = runner.normalize_registered_source(
        list(reversed(paths)),
        runner_label="ubuntu-24.04",
        source_read_authorized=True,
    )
    assert out == bars
    assert events[:2] == ["runtime", "pre_source"]
    first_scan = next(i for i, item in enumerate(events) if item.startswith("scan:"))
    last_sha = max(i for i, item in enumerate(events) if item.startswith("sha:"))
    assert last_sha < first_scan
    assert events[-2:] == ["manifest", "normalize"]


def test_training_return_extraction_uses_endpoint_inside_train_and_resets_at_gap():
    t = datetime(2020, 1, 1, tzinfo=UTC)
    stamps = [
        t - timedelta(hours=1),
        t,
        t + timedelta(hours=1),
        t + timedelta(hours=3),
        t + timedelta(hours=4),
    ]
    arm = ArmBars(
        "PROJECT_GAP_PRESERVING",
        tuple(_bar(stamp, 100 + i) for i, stamp in enumerate(stamps)),
        tuple(False for _ in stamps),
        (0, 0, 0, 1, 1),
        (0, 1, 2, 0, 1),
    )
    segments = runner._training_return_segments(
        arm,
        train_start=t,
        train_end=t + timedelta(hours=5),
    )
    assert [len(segment) for segment in segments] == [2, 1]


def test_one_fold_wires_registered_components_and_zero_based_fold_index(monkeypatch):
    test_start = datetime(2021, 1, 1, tzinfo=UTC)
    bars = tuple(
        _bar(test_start - timedelta(hours=24) + timedelta(hours=i), 100 + i / 10)
        for i in range(30)
    )
    arm = ArmBars(
        "PAPER_FILL",
        bars,
        tuple(False for _ in bars),
        tuple(0 for _ in bars),
        tuple(range(len(bars))),
    )
    fold = {
        "fold": 1,
        "fold_index": 0,
        "train_start": datetime(2020, 4, 1, tzinfo=UTC),
        "validation_start": datetime(2020, 10, 1, tzinfo=UTC),
        "test_start": test_start,
        "test_end": test_start + timedelta(hours=4),
    }

    calls = []
    monkeypatch.setattr(
        runner,
        "construct_missing_data_arm",
        lambda *args, **kwargs: (calls.append("arm"), arm)[1],
    )
    monkeypatch.setattr(
        runner,
        "compute_base_ohlcv_features",
        lambda value: (calls.append("base"), SimpleNamespace())[1],
    )
    candidates = SimpleNamespace(target_next_hour=np.zeros(len(bars)))
    monkeypatch.setattr(
        runner,
        "compute_ta_candidates",
        lambda value: (calls.append("ta"), candidates)[1],
    )
    selection = SimpleNamespace(selected_names=tuple(f"F{i}" for i in range(10)))
    monkeypatch.setattr(
        runner,
        "select_four_block_features",
        lambda *args, **kwargs: (calls.append("select"), selection)[1],
    )
    monkeypatch.setattr(
        runner,
        "_training_return_segments",
        lambda *args, **kwargs: (calls.append("train_returns"), (np.array([0.1, -0.1]),))[1],
    )
    fit = SimpleNamespace(
        params=np.array([0.0]),
        order=(1, 1, 1),
        aic=1.0,
    )
    monkeypatch.setattr(
        runner,
        "select_best_order",
        lambda segments: (calls.append("egarch_fit"), fit)[1],
    )
    monkeypatch.setattr(
        runner,
        "build_egarch_features",
        lambda *args, **kwargs: (calls.append("egarch_replay"), SimpleNamespace())[1],
    )
    monkeypatch.setattr(
        runner,
        "assemble_deployed_matrix",
        lambda **kwargs: (calls.append("matrix"), SimpleNamespace())[1],
    )

    train = SplitRows(
        np.array([0, 1]),
        np.ones((2, 28)),
        np.array([0.001, -0.001]),
        (bars[0].timestamp, bars[1].timestamp),
    )
    validation = SplitRows(
        np.array([2, 3]),
        np.ones((2, 28)),
        np.array([0.002, -0.002]),
        (bars[2].timestamp, bars[3].timestamp),
    )
    test = SplitRows(
        np.array([24, 25, 26]),
        np.ones((3, 28)),
        np.array([0.001, -0.001, 0.002]),
        (bars[24].timestamp, bars[25].timestamp, bars[26].timestamp),
    )
    split_queue = [train, validation, test]

    def fake_split(*args, **kwargs):
        calls.append("split")
        return split_queue.pop(0)

    monkeypatch.setattr(runner, "eligible_split_rows", fake_split)

    model_selection = SimpleNamespace(selected=SimpleNamespace(trial_number=7))

    def fake_tune(**kwargs):
        calls.append("tune")
        assert kwargs["fold_index"] == 0
        assert kwargs["arm"] == "PAPER_FILL"
        return model_selection

    monkeypatch.setattr(runner, "tune_fold", fake_tune)

    forecast = SimpleNamespace(
        forecasts_raw=np.array([0.003, -0.003, 0.004]),
        random_state=123456,
    )
    monkeypatch.setattr(
        runner,
        "final_refit_and_forecast",
        lambda **kwargs: (calls.append("forecast"), forecast)[1],
    )

    out = runner._run_arm_fold([bars[0]], arm_name="PAPER_FILL", fold=fold)
    assert out.fold_number == 1
    assert out.fold_index == 0
    assert out.forecast_count == 3
    assert out.selected_trial_index == 7
    assert out.final_model_seed == 123456
    assert calls == [
        "arm",
        "base",
        "ta",
        "select",
        "train_returns",
        "egarch_fit",
        "egarch_replay",
        "matrix",
        "split",
        "split",
        "split",
        "tune",
        "forecast",
    ]


def test_full_orchestrator_fixes_11x2_order_and_168_24_72_bootstrap_order(monkeypatch):
    dummy_bar = _bar(datetime(2017, 12, 1, tzinfo=UTC), 100)
    calls = []

    def fake_fold(bars, *, arm_name, fold):
        calls.append((arm_name, fold["fold"], fold["fold_index"]))
        arr_b = np.array([0.0001, -0.0001, 0.0002])
        arr_c = np.array([0.0002, -0.00005, 0.00025])
        return runner.FoldExecution(
            arm=arm_name,
            fold_number=fold["fold"],
            fold_index=fold["fold_index"],
            forecast_sha256=f"hash-{arm_name}-{fold['fold']}",
            forecast_count=3,
            selected_features=tuple(f"F{i}" for i in range(10)),
            egarch_order=(1, 1, 1),
            egarch_aic=1.0,
            selected_trial_index=0,
            final_model_seed=1,
            baseline_segments=(arr_b,),
            cost_aware_segments=(arr_c,),
            buy_hold_segments=(arr_b,),
            momentum_segments=(arr_b,),
            baseline_turnover=2.0,
            cost_aware_turnover=1.0,
            baseline_completed_trades=1,
            cost_aware_completed_trades=1,
        )

    monkeypatch.setattr(runner, "_run_arm_fold", fake_fold)

    bootstrap_calls = []

    def fake_bootstrap(baseline, cost, *, block_hours, arm_index, draws=10_000):
        bootstrap_calls.append((arm_index, block_hours))
        return BootstrapResult(
            True,
            0.0001,
            0.0001,
            11,
            0.01,
            (0.00001, 0.0002),
            True,
            0.1,
            (0.01, 0.2),
        )

    monkeypatch.setattr(runner, "paired_segment_bootstrap", fake_bootstrap)
    monkeypatch.setattr(
        runner,
        "performance_metrics",
        lambda values: {
            "N": len(values),
            "total_return": 0.01,
            "ARC": 0.1,
            "ASD": 0.1,
            "SHARPE": 1.0,
            "max_drawdown": -0.01,
        },
    )
    captured = {}

    def fake_classify(summaries):
        captured.update(summaries)
        return "BOUNDED_H2_NOT_REPLICATED"

    monkeypatch.setattr(runner, "classify_success", fake_classify)

    result = runner.run_from_normalized_bars([dummy_bar])
    assert calls == [
        (arm, fold, fold - 1)
        for arm in ("PAPER_FILL", "PROJECT_GAP_PRESERVING")
        for fold in range(1, 12)
    ]
    assert bootstrap_calls == [
        (0, 168), (0, 24), (0, 72),
        (1, 168), (1, 24), (1, 72),
    ]
    assert result["fold_index_base"] == 0
    assert result["trial_index_base"] == 0
    assert result["execution_order"]["bootstrap_hours"] == [168, 24, 72]
    assert len(result["arms"]["PAPER_FILL"]["folds"]) == 11
    assert len(result["arms"]["PROJECT_GAP_PRESERVING"]["folds"]) == 11
    assert set(captured) == {"PAPER_FILL", "PROJECT_GAP_PRESERVING"}
