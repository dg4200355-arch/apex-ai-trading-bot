import pandas as pd

from tools import paper_broker as pb


def test_position_sizing_keeps_cash_reserve_and_no_leverage():
    state = pb.new_broker_state("2026-08-09T00:00:00+00:00")
    account = state["accounts"]["US"]
    fill, err = pb.execute_buy(account, "AAA", "US", "C1", 100.0, "2026-08-10")
    assert err is None
    assert fill["qty"] > 0
    assert account["cash"] >= account["initial_cash"] * pb.CASH_RESERVE_FRACTION
    assert account["cash"] >= 0
    assert fill["qty"] * fill["price"] + fill["fee"] <= account["initial_cash"] * pb.POSITION_FRACTION + 1e-6


def test_flat_roundtrip_loses_costs_and_slippage():
    state = pb.new_broker_state("2026-08-09T00:00:00+00:00")
    account = state["accounts"]["US"]
    buy, err = pb.execute_buy(account, "AAA", "US", "C1", 100.0, "2026-08-10")
    assert err is None and buy is not None
    sell, err = pb.execute_sell(account, "AAA", 100.0)
    assert err is None and sell is not None
    assert sell["realized_pnl"] < 0
    assert account["completed_trades"] == 1
    assert "AAA" not in account["positions"]


def test_cluster_gate_blocks_duplicate_risk():
    state = pb.new_broker_state("2026-08-09T00:00:00+00:00")
    account = state["accounts"]["US"]
    fill, err = pb.execute_buy(account, "V", "US", "C2", 100.0, "2026-08-10")
    assert err is None and fill is not None
    assert not pb.cluster_is_free(account, "C2")
    assert pb.cluster_is_free(account, "C1")


def test_same_cluster_simultaneous_signals_only_first_admission_fills(monkeypatch):
    state = pb.new_broker_state("2026-08-09T00:00:00+00:00")
    events = pd.DataFrame([
        {"날짜": "2026-08-10", "시장": "US", "코드": "MA", "현재포지션": "LONG"},
        {"날짜": "2026-08-10", "시장": "US", "코드": "V", "현재포지션": "LONG"},
    ])
    candidates = {
        "V": {"frozen_verified": True, "quarantine_reason": None, "등록시각UTC": "2026-08-09T01:00:00+00:00"},
        "MA": {"frozen_verified": True, "quarantine_reason": None, "등록시각UTC": "2026-08-09T02:00:00+00:00"},
    }
    clusters = {"V": "C2", "MA": "C2"}

    monkeypatch.setattr(pb, "price_on", lambda cache, ticker, date, field: 100.0)
    orders, accounts = pb.process_events(state, events, candidates, clusters)

    filled = [x for x in orders if x["구분"] == "BUY" and x["상태"] == "FILLED"]
    blocked = [x for x in orders if x["구분"] == "BUY" and x["상태"] == "BLOCKED"]
    assert len(filled) == 1
    assert filled[0]["코드"] == "V"
    assert len(blocked) == 1
    assert blocked[0]["코드"] == "MA"
    assert blocked[0]["사유"] == "CLUSTER_OCCUPIED"
    assert set(state["accounts"]["US"]["positions"]) == {"V"}
    assert len(accounts) == 1


def test_state_schema_is_stable_across_logic_versions():
    state = pb.new_broker_state("2026-08-09T00:00:00+00:00")
    assert state["schema"] == pb.STATE_SCHEMA
    assert state["accounts"]["KR"]["initial_cash"] == 10_000_000.0
    assert state["accounts"]["US"]["initial_cash"] == 10_000.0
