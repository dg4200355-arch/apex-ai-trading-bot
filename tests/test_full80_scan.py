import numpy as np

from tools.autonomous_scan import FAMILY_SIZE, bh_qvalues


def test_family_size_is_full_universe():
    assert FAMILY_SIZE == 80


def test_full80_adjustment_is_not_looser_than_small_family():
    p = np.array([0.01, 0.02, 0.05, 0.10])
    q_small = bh_qvalues(p, family_size=4)
    q_full = bh_qvalues(p, family_size=80)
    assert np.all(q_full >= q_small - 1e-12)


def test_full80_adjustment_rejects_marginal_apparent_discovery():
    p = np.array([0.02, 0.03, 0.04])
    q = bh_qvalues(p, family_size=80)
    assert np.all(q > 0.20)
