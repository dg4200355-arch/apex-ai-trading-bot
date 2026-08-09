import numpy as np
import pandas as pd

from tools.paper_forward import FEE, reconcile_verifications, replay_unseen_bars


def base_state():
    return {
        "종목": "TEST",
        "코드": "TST",
        "시장": "US",
        "전략": "반전",
        "전략파라미터": {"bb": 0.25, "rsi": 40},
        "position": False,
        "entry_price": None,
        "entry_date": None,
        "pending_date": "2026-08-03",
        "pending_signal": True,
        "realized_equity": 1.0,
        "completed_trades": 0,
        "wins": 0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "trade_returns": [],
        "max_mark_equity": 1.0,
        "forward_mdd": 0.0,
        "observations": 1,
        "last_signal_date": "2026-08-03",
        "frozen_verified": True,
        "verification_time_utc": "2026-08-01T00:00:00+00:00",
        "verification_effective_after_date": "2026-08-01",
        "verification_revoked_after_date": None,
        "quarantine_reason": None,
        "model_cutoff": "2026-08-01",
    }


def frame(opens, closes):
    idx = pd.date_range("2026-08-03", periods=len(opens), freq="B")
    raw = pd.DataFrame({"Open": opens, "Close": closes}, index=idx)
    live = raw.copy()
    return idx, raw, live


def test_replays_every_missed_market_bar_and_executes_in_order():
    idx, raw, live = frame([100.0, 110.0, 120.0, 90.0], [100.0, 115.0, 118.0, 92.0])
    s = base_state()
    signals = pd.Series([True, True, False, False], index=idx)
    rows = replay_unseen_bars(s, raw, live, signals, idx[1:], "2026-08-09T00:00:00+00:00")
    assert len(rows) == 3
    assert [r["신호기준일"] for r in rows] == [d.date().isoformat() for d in idx[1:]]
    assert s["observations"] == 4
    assert s["completed_trades"] == 1
    assert s["position"] is False
    expected_trade = 90.0 / 110.0 - 1 - 2 * FEE
    assert np.isclose(s["trade_returns"][-1], expected_trade)
    assert np.isclose(s["realized_equity"], 1 + expected_trade)


def test_gap_before_next_open_is_not_credited_as_profit():
    idx, raw, live = frame([100.0, 200.0], [100.0, 200.0])
    s = base_state()
    signals = pd.Series([True, True], index=idx)
    rows = replay_unseen_bars(s, raw, live, signals, [idx[1]], "2026-08-09T00:00:00+00:00")
    assert len(rows) == 1
    assert s["position"] is True
    assert np.isclose(s["entry_price"], 200.0)
    assert rows[0]["전진누적수익"] < 0.0
    assert rows[0]["전진누적수익"] > -0.01


def test_same_signal_does_not_create_extra_trades():
    idx, raw, live = frame([100.0, 101.0, 102.0, 103.0], [100.0, 101.5, 102.5, 103.5])
    s = base_state()
    signals = pd.Series(True, index=idx)
    replay_unseen_bars(s, raw, live, signals, idx[1:], "2026-08-09T00:00:00+00:00")
    assert s["position"] is True
    assert s["completed_trades"] == 0
    assert s["observations"] == 4


def test_candidate_removed_from_primary_is_revoked_after_current_cutoff():
    state = {"TST": base_state()}
    primary = pd.DataFrame([{
        "코드": "OTHER",
        "최종등급": "B",
        "데이터기준일": "2026-08-07",
        "엔진버전": "8.5-frozen-primary",
    }])
    confirmation = pd.DataFrame()
    rows = reconcile_verifications(state, primary, confirmation, "2026-08-09T00:00:00+00:00")
    s = state["TST"]
    assert s["frozen_verified"] is False
    assert s["verification_revoked_after_date"] == "2026-08-07"
    assert "not present" in s["quarantine_reason"]
    assert len(rows) == 1
    assert rows[0]["업데이트"] == "VERIFICATION_UPDATE"


def test_new_confirmation_becomes_effective_only_after_cutoff():
    s = base_state()
    s["frozen_verified"] = False
    s["verification_time_utc"] = None
    s["verification_effective_after_date"] = None
    s["quarantine_reason"] = "awaiting"
    state = {"TST": s}
    primary = pd.DataFrame([{
        "코드": "TST",
        "최종등급": "B",
        "데이터기준일": "2026-08-07",
        "엔진버전": "8.5-frozen-primary",
    }])
    confirmation = pd.DataFrame([{
        "코드": "TST",
        "전략": "반전",
        "전략파라미터": '{"bb": 0.25, "rsi": 40}',
        "2차통과": "✅",
        "확인엔진": "8.5-frozen-confirm",
        "보류사유": "-",
    }])
    rows = reconcile_verifications(state, primary, confirmation, "2026-08-09T00:00:00+00:00")
    s = state["TST"]
    assert s["frozen_verified"] is True
    assert s["verification_effective_after_date"] == "2026-08-07"
    assert s["verification_revoked_after_date"] is None
    assert s["quarantine_reason"] is None
    assert len(rows) == 1
