"""Frozen AMS-DEP V2 synthetic DGP construction.

Pure synthetic generation only. No market-data loaders are imported here.
Calibration/holdout authorization is enforced by the runner, not this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

UINT32_MAX = 4294967295
VERSION = 2
ASSETS = ("BTC", "ETH")
STATES = np.array(["LOW", "NORMAL", "HIGH"])


@dataclass(frozen=True)
class AssetSample:
    x: np.ndarray
    y: np.ndarray
    years: np.ndarray
    states: np.ndarray
    hours: np.ndarray
    segments: np.ndarray


def _rng(root: int, dgp_index: int, outer_index: int, shock_index: int,
         year_index: int, channel_index: int) -> np.random.Generator:
    seed = np.random.SeedSequence([
        int(root), VERSION, int(dgp_index), int(outer_index), int(shock_index),
        UINT32_MAX, UINT32_MAX, int(year_index), int(channel_index),
    ])
    return np.random.Generator(np.random.PCG64(seed))


def _calendar_for_year(year: int, n: int, state_block_hours: int):
    # 2017-01-01 UTC hours without datetime dependencies or timezone ambiguity.
    import datetime as _dt
    start = int(_dt.datetime(year, 1, 1, tzinfo=_dt.timezone.utc).timestamp() // 3600)
    hours = start + np.arange(n, dtype=np.int64)
    states = STATES[(np.arange(n) // state_block_hours) % 3]
    years = np.full(n, year, dtype=np.int64)
    return years, states, hours


def _correlated_normals(root, dgp_index, outer_index, year_index, length, rho):
    g0 = _rng(root, dgp_index, outer_index, 0, year_index, 0).standard_normal(length)
    g1 = _rng(root, dgp_index, outer_index, 1, year_index, 0).standard_normal(length)
    z = np.empty((length, 2), dtype=np.float64)
    z[:, 0] = g0
    z[:, 1] = rho * g0 + np.sqrt(1.0 - rho * rho) * g1
    return z


def _base_returns(case, root, dgp_index, outer_index, year_index, year, config):
    p = config["v1_retained_scientific_parameters"]
    burn = int(p["burn_in"])
    n = int(p["observations_per_year"])
    length = burn + n + 1
    rho = float(p["asset_correlation"])
    sd = float(p["innovation_sd"])
    block = int(p["state_block_hours"])
    z = _correlated_normals(root, dgp_index, outer_index, year_index, length, rho)
    state_index = ((np.arange(length) - 1 - burn) // block) % 3

    if case == "iid_null" or case in ("irregular_null", "asynchronous_null"):
        return sd * z

    if case == "heteroskedastic_null":
        return np.array([0.005, 0.01, 0.03], dtype=np.float64)[state_index, None] * z

    if case == "student_t5_null":
        q = _rng(root, dgp_index, outer_index, 2, year_index, 1).chisquare(5, size=length)
        return sd * np.sqrt(3.0 / q)[:, None] * z

    if case == "volatility_break_null":
        sigma = np.full(length, 0.01, dtype=np.float64)
        eligible_sigma = np.empty(n + 1, dtype=np.float64)
        eligible_sigma[:500] = 0.005
        eligible_sigma[500:1000] = 0.01
        eligible_sigma[1000:1500] = 0.03
        eligible_sigma[1500:2001] = 0.01
        sigma[burn:burn + n + 1] = eligible_sigma
        return sigma[:, None] * z

    if case == "bid_ask_bounce":
        errors = np.empty((length + 1, 2), dtype=np.float64)
        # Frozen stream mapping: independent_shock_index = asset index,
        # channel_index = 2 for bid/ask signs.
        for asset in range(2):
            signs = _rng(root, dgp_index, outer_index, asset, year_index, 2).integers(
                0, 2, size=length + 1
            )
            errors[:, asset] = (2 * signs - 1) * 0.005
        return sd * z + np.diff(errors, axis=0)

    r = np.empty_like(z)
    previous = np.zeros(2, dtype=np.float64)
    variance = np.full(2, 0.0001, dtype=np.float64)
    for j in range(length):
        phi = 0.0
        sigma = sd
        if case == "stable_ar":
            phi = 0.10
        elif case == "time_ar":
            phi = 0.15 if year in (2017, 2019, 2021) else -0.15
        elif case == "state_ar":
            phi = (0.15, 0.0, -0.15)[int(state_index[j])]
        elif case == "garch_null":
            variance = 0.000005 + 0.10 * previous ** 2 + 0.85 * variance
            sigma = np.sqrt(variance)
        else:
            raise ValueError(f"unregistered V2 DGP: {case}")
        r[j] = phi * previous + sigma * z[j]
        previous = r[j]
    return r


def _observed_mask(case: str, asset: int, n: int, config: dict) -> np.ndarray:
    observed = np.ones(n + 1, dtype=bool)
    if case == "irregular_null":
        spec = config["added_dgps"]["irregular_null"]
        for start, end in spec["missing_hour_blocks_half_open"]:
            observed[int(start):int(end)] = False
        observed[np.asarray(spec["isolated_missing_offsets"], dtype=int)] = False
    elif case == "asynchronous_null":
        spec = config["added_dgps"]["asynchronous_null"]
        modulus = int(spec["btc_missing_modulus"] if asset == 0 else spec["eth_missing_modulus"])
        observed[np.arange(n + 1) % modulus == 0] = False
        if asset == 1:
            start, end = spec["eth_additional_missing_block_half_open"]
            observed[int(start):int(end)] = False
    return observed


def _segment_for_offsets(case: str, asset: int, year_index: int, offsets: np.ndarray) -> np.ndarray:
    if case == "irregular_null":
        phase = (offsets >= 744).astype(np.int64) + (offsets >= 1464).astype(np.int64)
        return year_index * 3 + phase
    if case == "asynchronous_null" and asset == 1:
        phase = (offsets >= 1024).astype(np.int64)
        return year_index * 2 + phase
    return np.full(len(offsets), year_index, dtype=np.int64)


def simulate_case(case: str, dgp_index: int, outer_index: int, config: dict,
                  data_root: int) -> tuple[AssetSample, AssetSample]:
    """Generate one two-asset outer replication under the frozen V2 DGP."""
    cases = config["cases"]
    if cases[dgp_index] != case:
        raise ValueError("DGP index/case mismatch")
    p = config["v1_retained_scientific_parameters"]
    years_list = list(p["years"])
    n = int(p["observations_per_year"])
    burn = int(p["burn_in"])
    state_block = int(p["state_block_hours"])

    per_asset = [
        {"x": [], "y": [], "years": [], "states": [], "hours": [], "segments": []}
        for _ in ASSETS
    ]

    for year_index, year in enumerate(years_list):
        r = _base_returns(case, data_root, dgp_index, outer_index, year_index, year, config)
        full_x = r[burn:burn + n]
        full_y = r[burn + 1:burn + n + 1]
        cal_years, cal_states, cal_hours = _calendar_for_year(year, n, state_block)

        for asset in range(2):
            observed = _observed_mask(case, asset, n, config)
            keep = observed[:n] & observed[1:n + 1]
            offsets = np.flatnonzero(keep).astype(np.int64)
            target = per_asset[asset]
            target["x"].append(full_x[keep, asset])
            target["y"].append(full_y[keep, asset])
            target["years"].append(cal_years[keep])
            target["states"].append(cal_states[keep])
            target["hours"].append(cal_hours[keep])
            target["segments"].append(_segment_for_offsets(case, asset, year_index, offsets))

    result = []
    for values in per_asset:
        result.append(AssetSample(
            x=np.concatenate(values["x"]),
            y=np.concatenate(values["y"]),
            years=np.concatenate(values["years"]),
            states=np.concatenate(values["states"]),
            hours=np.concatenate(values["hours"]),
            segments=np.concatenate(values["segments"]),
        ))
    return tuple(result)
