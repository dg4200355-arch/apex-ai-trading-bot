import pandas as pd

from tools import broker_health as bh
from tools import paper_broker as pb


def test_clean_new_state_passes_health_check():
    state = pb.new_broker_state("2026-08-09T00:00:00+00:00")
    assert bh.validate_state(state, pd.DataFrame()) == []


def test_duplicate_cluster_is_rejected():
    state = pb.new_broker_state("2026-08-09T00:00:00+00:00")
    a = state["accounts"]["US"]
    a["positions"] = {
        "V": {"qty": 1, "entry_price": 100.0, "cost_total": 100.2, "cluster": "C2"},
        "MA": {"qty": 1, "entry_price": 110.0, "cost_total": 110.2, "cluster": "C2"},
    }
    errors = bh.validate_state(state, pd.DataFrame())
    assert "US:duplicate-correlation-cluster" in errors


def test_drawdown_without_halt_is_rejected():
    state = pb.new_broker_state("2026-08-09T00:00:00+00:00")
    a = state["accounts"]["US"]
    a["max_drawdown"] = -0.12
    a["risk_halt"] = False
    errors = bh.validate_state(state, pd.DataFrame())
    assert "US:drawdown-halt-missing" in errors


def test_duplicate_filled_order_key_is_rejected():
    state = pb.new_broker_state("2026-08-09T00:00:00+00:00")
    orders = pd.DataFrame([
        {"체결일": "2026-08-10", "시장": "US", "코드": "V", "구분": "BUY", "상태": "FILLED"},
        {"체결일": "2026-08-10", "시장": "US", "코드": "V", "구분": "BUY", "상태": "FILLED"},
    ])
    errors = bh.validate_state(state, orders)
    assert "duplicate-filled-order-key" in errors
