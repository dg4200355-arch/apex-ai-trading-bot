import numpy as np

from tools.promotion_gate import (
    bh_qvalues,
    bootstrap_positive_probability,
    sign_test_pvalue,
    stress_compounded_return,
)


def test_bootstrap_strong_positive_trades_have_high_support():
    trades = [0.04, 0.03, 0.05, 0.02, 0.06, 0.01]
    p = bootstrap_positive_probability(trades, samples=1000, seed=7)
    assert p > 0.95


def test_bootstrap_mixed_negative_profile_is_not_overconfident():
    trades = [0.01, -0.05, 0.01, -0.04, 0.01, -0.03]
    p = bootstrap_positive_probability(trades, samples=1000, seed=7)
    assert p < 0.50


def test_extra_transaction_cost_reduces_compounded_result():
    trades = [0.02, 0.015, -0.005, 0.01, 0.02]
    original = float(np.prod(1 + np.asarray(trades)) - 1)
    stressed = stress_compounded_return(trades)
    assert np.isfinite(stressed)
    assert stressed < original


def test_bootstrap_requires_minimum_trade_sample():
    assert np.isnan(bootstrap_positive_probability([0.1, 0.1, 0.1]))


def test_exact_sign_test_rewards_consistent_positive_trades():
    p = sign_test_pvalue([0.01, 0.02, 0.03, 0.04, 0.05])
    assert np.isclose(p, 1 / 32)


def test_exact_sign_test_is_not_significant_for_mixed_direction():
    p = sign_test_pvalue([0.02, -0.01, 0.03, -0.02, 0.01, -0.01])
    assert p >= 0.50


def test_more_tracked_candidates_cannot_make_q_value_looser():
    p = np.array([0.03125, 0.10])
    q_two = bh_qvalues(p, family_size=2)
    q_twenty = bh_qvalues(p, family_size=20)
    assert np.all(q_twenty >= q_two - 1e-12)
