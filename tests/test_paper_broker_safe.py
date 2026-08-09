import pytest

from tools import paper_broker_safe as safe


def test_execution_error_gate_detects_only_error_status():
    rows = [
        {"상태": "FILLED", "코드": "A"},
        {"상태": "BLOCKED", "코드": "B"},
        {"상태": "ERROR", "코드": "C"},
    ]
    errors = safe.execution_errors(rows)
    assert len(errors) == 1
    assert errors[0]["코드"] == "C"


def test_no_execution_errors_is_commit_safe():
    assert safe.execution_errors([{"상태": "FILLED"}, {"상태": "BLOCKED"}]) == []


def held_state():
    state = safe.pb.new_broker_state("2026-08-09T00:00:00+00:00")
    account = state["accounts"]["US"]
    fill, err = safe.pb.execute_buy(account, "AAA", "US", "C1", 100.0, "2026-08-10")
    assert err is None and fill is not None
    state["corporate_actions_applied"] = []
    return state, account


def test_dividend_entitlement_does_not_increase_preorder_cash(monkeypatch):
    state, account = held_state()
    qty = account["positions"]["AAA"]["qty"]
    cash_before = account["cash"]
    monkeypatch.setattr(safe.raw, "_action_values", lambda cache, ticker, date: (1.25, 0.0))

    rows, entitlements = safe.prepare_preopen_actions(
        state, account, "AAA", "2026-08-11", {}, "now", "US", "C1"
    )
    assert rows == []
    assert len(entitlements) == 1
    assert entitlements[0]["qty"] == qty
    assert account["cash"] == pytest.approx(cash_before)
    assert "AAA|2026-08-11|DIVIDEND" not in state["corporate_actions_applied"]

    dividend_rows = safe.settle_dividend_entitlements(state, account, entitlements, "now")
    assert account["cash"] == pytest.approx(cash_before + qty * 1.25)
    assert len(dividend_rows) == 1
    assert dividend_rows[0]["구분"] == "DIVIDEND"
    assert dividend_rows[0]["사유"] == "EX_DATE_ENTITLEMENT_POST_ORDER_CREDIT"
    assert dividend_rows[0]["브로커"] == safe.raw.VERSION
    assert "AAA|2026-08-11|DIVIDEND" in state["corporate_actions_applied"]


def test_dividend_settlement_is_idempotent(monkeypatch):
    state, account = held_state()
    monkeypatch.setattr(safe.raw, "_action_values", lambda cache, ticker, date: (1.0, 0.0))
    _, ents = safe.prepare_preopen_actions(state, account, "AAA", "2026-08-11", {}, "now", "US", "C1")
    before = account["cash"]
    first = safe.settle_dividend_entitlements(state, account, ents, "now")
    after_first = account["cash"]
    second = safe.settle_dividend_entitlements(state, account, ents, "now")
    assert len(first) == 1
    assert second == []
    assert after_first > before
    assert account["cash"] == pytest.approx(after_first)


def test_simultaneous_dividend_and_split_fails_closed(monkeypatch):
    state, account = held_state()
    monkeypatch.setattr(safe.raw, "_action_values", lambda cache, ticker, date: (1.0, 2.0))
    with pytest.raises(RuntimeError, match="simultaneous dividend/split"):
        safe.prepare_preopen_actions(state, account, "AAA", "2026-08-11", {}, "now", "US", "C1")


def test_shared_helper_version_is_not_left_as_raw_broker_version():
    assert safe.pb.VERSION == safe.LEGACY_CORE_VERSION
    row = safe.order_row("now", "2026-08-11", "US", "AAA", "BUY", "BLOCKED", "TEST", "C1")
    assert row["브로커"] == safe.raw.VERSION
