import numpy as np
import pandas as pd

from engine import StrategyChoice, split_holdout
from tools import autonomous_scan as scan
from tools import stress_confirm as confirm


def dummy_data(n=100):
    idx = pd.date_range("2025-01-01", periods=n, freq="B")
    d = pd.DataFrame(index=idx)
    d["target"] = np.arange(n) % 2
    d["Close"] = np.linspace(100, 120, n)
    return d


def test_core_split_has_exact_future_bar_embargo():
    data = dummy_data(100)
    pretest, embargo, test = split_holdout(data, future=5, train_fraction=0.75)
    assert len(pretest) == 70
    assert len(embargo) == 5
    assert len(test) == 25
    assert pretest.index[-1] < embargo.index[0] < test.index[0]


def test_freeze_selection_never_sees_embargo_rows(monkeypatch):
    data = dummy_data(100)
    seen = {}

    def fake_rule(pretest, full, fee):
        seen["len"] = len(pretest)
        seen["last"] = pretest.index[-1]
        return StrategyChoice("추세", {"fast": 8, "slow": 55, "rsi_max": 76, "vol_min": 0.65}, 1.0, 0.1, 1.0, 10)

    monkeypatch.setattr(scan, "select_rule", fake_rule)
    monkeypatch.setattr(scan, "select_ai", lambda *args, **kwargs: None)
    choice = scan.freeze_selected_choice(data, "추세")

    assert choice.kind == "추세"
    assert seen["len"] == 70
    assert seen["last"] == data.index[69]


def test_confirmation_uses_same_purged_boundary():
    data = dummy_data(100)
    pretest, embargo, test = confirm.primary_holdout_split(data)
    assert len(pretest) == 70
    assert len(embargo) == confirm.FUTURE == 5
    assert len(test) == 25
    assert pretest.index[-1] == data.index[69]
    assert test.index[0] == data.index[75]
