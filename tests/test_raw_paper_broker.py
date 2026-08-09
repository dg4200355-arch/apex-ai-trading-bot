import pandas as pd
import pytest

from tools import paper_broker as legacy
from tools import paper_broker_raw as raw


def flat_state():
    return legacy.new_broker_state("2026-08-09T00:00:00+00:00")


def held_state():
    s = flat_state()
    fill, err = legacy.execute_buy(s["accounts"]["US"], "AAA", "US", "C1", 100.0, "2026-08-10")
    assert err is None and fill
    return s


def test_flat_legacy_state_migrates_to_raw_basis():
    s = flat_state()
    changed = raw.migrate_state_to_raw(s)
    assert changed is True
    assert s["price_basis"] == raw.PRICE_BASIS
    assert s["version"] == raw.VERSION
    assert s["corporate_actions_applied"] == []


def test_open_adjusted_position_cannot_silently_migrate():
    s = held_state()
    with pytest.raises(RuntimeError, match="cannot migrate adjusted-price holdings"):
        raw.migrate_state_to_raw(s)


def test_raw_frame_requires_execution_basis(monkeypatch):
    idx = pd.date_range("2026-08-10", periods=2, freq="B")
    d = pd.DataFrame({
        "Open": [100.0, 101.0], "High": [102.0, 103.0], "Low": [99.0, 100.0],
        "Close": [101.0, 102.0], "Volume": [1000, 1100],
    }, index=idx)
    d.attrs["price_basis"] = "RAW_EXECUTION"
    monkeypatch.setattr(raw, "download_trade_ohlcv", lambda ticker, period=None: d.copy())
    cache = {}
    assert raw.raw_price_on(cache, "AAA", "2026-08-10", "Open") == 100.0


def _action_frame(dividend=0.0, split=0.0):
    idx = pd.to_datetime(["2026-08-11"])
    return pd.DataFrame({"Dividends": [dividend], "Stock Splits": [split]}, index=idx)


def test_dividend_credits_preexisting_holder_once(monkeypatch):
    s = held_state()
    raw.migrate_state_to_raw(s) if not s["accounts"]["US"]["positions"] else None
    # Mark as raw explicitly for this synthetic corporate-action unit test.
    s["price_basis"] = raw.PRICE_BASIS
    s["corporate_actions_applied"] = []
    account = s["accounts"]["US"]
    qty = account["positions"]["AAA"]["qty"]
    before = account["cash"]
    monkeypatch.setattr(raw, "download_trade_actions", lambda ticker, period=None: _action_frame(dividend=1.25))
    rows1 = raw.apply_corporate_actions(s, account, "AAA", "2026-08-11", {}, "now", "US", "C1")
    rows2 = raw.apply_corporate_actions(s, account, "AAA", "2026-08-11", {}, "now", "US", "C1")
    assert account["cash"] == pytest.approx(before + qty * 1.25)
    assert len(rows1) == 1 and rows1[0]["구분"] == "DIVIDEND"
    assert rows2 == []


def test_integer_split_adjusts_quantity_and_entry_price(monkeypatch):
    s = held_state()
    s["price_basis"] = raw.PRICE_BASIS
    s["corporate_actions_applied"] = []
    account = s["accounts"]["US"]
    pos = account["positions"]["AAA"]
    old_qty, old_entry, old_cost = pos["qty"], pos["entry_price"], pos["cost_total"]
    monkeypatch.setattr(raw, "download_trade_actions", lambda ticker, period=None: _action_frame(split=2.0))
    rows = raw.apply_corporate_actions(s, account, "AAA", "2026-08-11", {}, "now", "US", "C1")
    assert pos["qty"] == old_qty * 2
    assert pos["entry_price"] == pytest.approx(old_entry / 2)
    assert pos["cost_total"] == pytest.approx(old_cost)
    assert rows[0]["구분"] == "SPLIT"


def test_fractional_split_fails_closed(monkeypatch):
    s = flat_state()
    account = s["accounts"]["US"]
    account["positions"]["AAA"] = {
        "ticker": "AAA", "market": "US", "cluster": "C1", "qty": 3,
        "entry_price": 100.0, "entry_fee": 1.0, "cost_total": 301.0,
        "entry_date": "2026-08-10", "last_price": 100.0,
    }
    s["corporate_actions_applied"] = []
    monkeypatch.setattr(raw, "download_trade_actions", lambda ticker, period=None: _action_frame(split=0.5))
    with pytest.raises(RuntimeError, match="cash-in-lieu"):
        raw.apply_corporate_actions(s, account, "AAA", "2026-08-11", {}, "now", "US", "C1")
