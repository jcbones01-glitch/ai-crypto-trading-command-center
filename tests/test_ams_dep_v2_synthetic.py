import json
from pathlib import Path

import numpy as np

from research_core.ams_dep_v2_synthetic import simulate_case


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "research/experiments/ams_dep_synthetic_core_v2.json"
TEST_ROOT = 314159265


def config():
    return json.loads(CONFIG.read_text())


def test_generator_is_reproducible_without_using_reserved_roots():
    cfg = config()
    assert TEST_ROOT not in set(cfg["data_roots"].values())
    a = simulate_case("iid_null", 0, 7, cfg, TEST_ROOT)
    b = simulate_case("iid_null", 0, 7, cfg, TEST_ROOT)
    for left, right in zip(a, b):
        np.testing.assert_array_equal(left.x, right.x)
        np.testing.assert_array_equal(left.y, right.y)
        np.testing.assert_array_equal(left.hours, right.hours)
        np.testing.assert_array_equal(left.segments, right.segments)
    c = simulate_case("iid_null", 0, 8, cfg, TEST_ROOT)
    assert not np.array_equal(a[0].x, c[0].x)


def test_regular_v1_cases_keep_10000_rows_and_five_segments():
    cfg = config()
    for index, case in enumerate(cfg["cases"][:7]):
        samples = simulate_case(case, index, 0, cfg, TEST_ROOT)
        for sample in samples:
            assert len(sample.x) == 10_000
            assert len(sample.y) == 10_000
            assert len(np.unique(sample.segments)) == 5
            assert np.all(np.diff(sample.hours[sample.segments == 0]) == 1)


def test_irregular_null_preserves_actual_hour_gaps_and_resets_only_long_blocks():
    cfg = config()
    index = cfg["cases"].index("irregular_null")
    btc, eth = simulate_case("irregular_null", index, 0, cfg, TEST_ROOT)
    assert len(btc.x) == len(eth.x) == 9_680
    np.testing.assert_array_equal(btc.hours, eth.hours)
    np.testing.assert_array_equal(btc.segments, eth.segments)
    assert len(np.unique(btc.segments)) == 15

    first_year = btc.years == 2017
    h = btc.hours[first_year]
    s = btc.segments[first_year]
    offsets = h - h.min()
    # Isolated missing observed hour 101 removes rows 100 and 101, but does
    # not create a declared segment reset. Actual elapsed hours remain visible.
    where = np.flatnonzero(np.diff(h) > 1)
    assert len(where) >= 1
    isolated = [i for i in where if h[i + 1] - h[i] == 3]
    assert isolated
    i = isolated[0]
    assert s[i] == s[i + 1]
    # Long block [720,744) creates a new declared segment after the gap.
    long_gap = np.flatnonzero(np.diff(h) >= 25)
    assert len(long_gap) == 2
    for i in long_gap:
        assert s[i] != s[i + 1]


def test_asynchronous_null_has_distinct_asset_support_and_exact_intersection():
    cfg = config()
    index = cfg["cases"].index("asynchronous_null")
    btc, eth = simulate_case("asynchronous_null", index, 0, cfg, TEST_ROOT)
    assert len(btc.x) == 9_795
    assert len(eth.x) == 9_650
    assert not np.array_equal(btc.hours, eth.hours)
    exact = np.intersect1d(btc.hours, eth.hours)
    assert len(exact) < len(btc.hours)
    assert len(exact) < len(eth.hours)
    # No row-index/nearest-time equivalence can reproduce the exact support.
    assert np.any(btc.hours[: min(len(btc.hours), len(eth.hours))] != eth.hours[: min(len(btc.hours), len(eth.hours))])
    assert len(np.unique(btc.segments)) == 5
    assert len(np.unique(eth.segments)) == 10


def test_student_t5_and_volatility_break_are_null_mean_stress_cases():
    cfg = config()
    t_index = cfg["cases"].index("student_t5_null")
    v_index = cfg["cases"].index("volatility_break_null")
    t = simulate_case("student_t5_null", t_index, 2, cfg, TEST_ROOT)[0]
    v = simulate_case("volatility_break_null", v_index, 2, cfg, TEST_ROOT)[0]
    assert abs(np.mean(t.y)) < 0.002
    assert abs(np.corrcoef(t.x, t.y)[0, 1]) < 0.08

    first = v.y[v.years == 2017]
    blocks = [first[:499], first[500:999], first[1000:1499], first[1500:1999]]
    stds = [float(np.std(x)) for x in blocks]
    assert stds[2] > 4 * stds[0]
    assert stds[2] > 2 * stds[1]


def test_registered_ar_alternatives_have_planted_direction():
    cfg = config()
    for case in ("stable_ar", "time_ar", "state_ar"):
        index = cfg["cases"].index(case)
        btc = simulate_case(case, index, 3, cfg, TEST_ROOT)[0]
        overall = float(np.corrcoef(btc.x, btc.y)[0, 1])
        if case == "stable_ar":
            assert overall > 0.04
        elif case == "time_ar":
            signs = []
            for year in cfg["v1_retained_scientific_parameters"]["years"]:
                mask = btc.years == year
                signs.append(np.sign(np.corrcoef(btc.x[mask], btc.y[mask])[0, 1]))
            assert signs == [1, -1, 1, -1, 1]
        else:
            corrs = {}
            for state in ("LOW", "NORMAL", "HIGH"):
                mask = btc.states == state
                corrs[state] = float(np.corrcoef(btc.x[mask], btc.y[mask])[0, 1])
            assert corrs["LOW"] > 0.05
            assert corrs["HIGH"] < -0.05
