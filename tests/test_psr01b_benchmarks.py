"""Synthetic tests for PSR-01B contextual benchmarks."""
import numpy as np
import pytest

from research_core.psr01b_benchmarks import (
    buy_and_hold_segments,
    momentum_24h_segments,
)


def test_buy_and_hold_enters_and_exits_each_gap_defined_segment():
    out = buy_and_hold_segments(
        [
            [0.0, 0.0],
            [0.0, 0.0, 0.0],
        ]
    )
    np.testing.assert_array_equal(out.positions, [1, 1, 1, 1, 1])
    assert out.turnover == 4.0
    assert out.completed_trades == 2
    assert out.returns.sum() == pytest.approx(-0.004)


def test_single_record_buy_and_hold_charges_entry_and_terminal_exit_once():
    out = buy_and_hold_segments([[0.0]])
    assert out.turnover == 2.0
    assert out.completed_trades == 1
    assert out.returns[0] == pytest.approx(-0.002)


def test_momentum_24h_is_unfiltered_sign_rule_with_gap_cash_restart():
    signals = [
        [0.1, -0.1, 0.2],
        [-0.2, 0.3],
    ]
    realized = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0],
    ]
    out = momentum_24h_segments(signals, realized)
    np.testing.assert_array_equal(out.positions, [1, 0, 1, 0, 1])
    # First segment: enter, exit, enter, forced terminal exit = 4.
    # Second segment: flat, enter, forced terminal exit = 2.
    assert out.turnover == 6.0
    assert out.completed_trades == 3
    assert out.returns.sum() == pytest.approx(-0.006)


def test_momentum_zero_signal_stays_flat():
    out = momentum_24h_segments([[0.0, 0.0]], [[0.01, -0.01]])
    np.testing.assert_array_equal(out.positions, [0, 0])
    assert out.turnover == 0.0
    assert out.completed_trades == 0
    np.testing.assert_array_equal(out.returns, [0.0, 0.0])
