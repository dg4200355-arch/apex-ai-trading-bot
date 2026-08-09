"""Forward-only paper tracker with immutable admission verification.

Strategy family/parameters stay frozen after admission. Every unseen completed bar
is replayed in order. A verification decision produced from data through close t is
applied only after t, so it can affect execution from the next market session but
never retroactively at open t. No live orders are placed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

from engine import atr, build_rule_signal, ema, fit_ai_predict, make_features, rsi
from market_data import download_ohlcv

PRIMARY = Path("reports/latest_validation.csv")
CONFIRM = Path("reports/latest_confirmation.csv")
STATE_PATH = Path("reports/paper_state.json")
LOG_PATH = Path("reports/paper_forward.csv")
SUMMARY_PATH = Path("reports/paper_forward.md")
FEE = 0.0015
TRACKER_VERSION = "paper-forward-1.3-verification-timing"
EXPECTED_PRIMARY_ENGINE = "8.5-frozen-primary"
EXPECTED_CONFIRM_ENGINE = "8.5-frozen-confirm"
ELIGIBLE_PRIMARY_GRADES = {"A", "B", "관찰"}


def dl(ticker: str, period: str = "2y") -> pd.DataFrame:
    return download_ohlcv(ticker, period=period)


def make_live_features(raw: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    d = raw[["Open", "High", "Low", "Close", "Volume"]].copy().sort_index()
    m = market["Close"].pct_change().rename("market_ret1")
    d = d.join(m, how="left").ffill()
    for n in [8, 20, 21, 55, 100, 200]:
        d[f"ema{n}"] = ema(d["Close"], n)
    d["rsi"] = rsi(d["Close"])
    macd = ema(d["Close"], 12) - ema(d["Close"], 26)
    sig = ema(macd, 9)
    d["macd"] = macd / d["Close"]
    d["hist"] = (macd - sig) / d["Close"]
    d["atr"] = atr(d)
    d["atr_pct"] = d["atr"] / d["Close"]
    mid = d["Close"].rolling(20).mean()
    sd = d["Close"].rolling(20).std()
    lo, hi = mid - 2 * sd, mid + 2 * sd
    d["bb_pos"] = (d["Close"] - lo) / (hi - lo).replace(0, np.nan)
    d["vol_ratio"] = d["Volume"] / d["Volume"].rolling(20).mean()
    d["volatility"] = d["Close"].pct_change().rolling(10).std()
    d["range_pct"] = (d["High"] - d["Low"]) / d["Close"]
    for n in [1, 3, 5, 10]:
        d[f"ret{n}"] = d["Close"].pct_change(n)
    d["ema8_21"] = d["ema8"] / d["ema21"] - 1
    d["ema21_55"] = d["ema21"] / d["ema55"] - 1
    d["ema55_200"] = d["ema55"] / d["ema200"] - 1
    d["market_ret5"] = (1 + d["market_ret1"]).rolling(5).apply(np.prod, raw=True) - 1
    d["relative5"] = d["ret5"] - d["market_ret5"]
    d["donchian20"] = d["High"].rolling(20).max().shift(1)
    d["donchian55"] = d["High"].rolling(55).max().shift(1)
    return d.replace([np.inf, -np.inf], np.nan).dropna()


def load_state() -> Dict[str, dict]:
    if not STATE_PATH.exists():
        return {}
    try:
        obj = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def save_state(state: Dict[str, dict]):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_log() -> pd.DataFrame:
    if not LOG_PATH.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(LOG_PATH)
    except Exception:
        return pd.DataFrame()


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or not path.stat().st_size:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def normalized_params(obj) -> str:
    if isinstance(obj, str):
        obj = json.loads(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def admission_matches(state_row: dict, confirmation_row: pd.Series) -> bool:
    try:
        return (
            str(state_row.get("전략")) == str(confirmation_row["전략"])
            and normalized_params(state_row.get("전략파라미터", {}))
            == normalized_params(str(confirmation_row["전략파라미터"]))
        )
    except Exception:
        return False


def mark_equity(s: dict, close_price: float) -> float:
    realized = float(s.get("realized_equity", 1.0))
    if bool(s.get("position")) and s.get("entry_price"):
        gross = close_price / float(s["entry_price"]) - 1
        return realized * (1 + gross - 2 * FEE)
    return realized


def _trade_pf(s: dict) -> float:
    gp = float(s.get("gross_profit", 0.0))
    gl = float(s.get("gross_loss", 0.0))
    trades = int(s.get("completed_trades", 0))
    if gl > 0:
        return gp / gl
    if trades > 0 and gp > 0:
        return np.inf
    return np.nan


def _record_trade(s: dict, tr: float):
    s["realized_equity"] = float(s.get("realized_equity", 1.0)) * (1 + tr)
    s["completed_trades"] = int(s.get("completed_trades", 0)) + 1
    returns = list(s.get("trade_returns", []))
    returns.append(float(tr))
    s["trade_returns"] = returns[-200:]
    if tr > 0:
        s["wins"] = int(s.get("wins", 0)) + 1
        s["gross_profit"] = float(s.get("gross_profit", 0.0)) + tr
    else:
        s["gross_loss"] = float(s.get("gross_loss", 0.0)) + abs(tr)


def _execute_pending_at_open(s: dict, open_price: float, date: pd.Timestamp):
    if s.get("pending_date") is None:
        return
    desired = bool(s.get("pending_signal"))
    position = bool(s.get("position"))
    if desired and not position:
        s["position"] = True
        s["entry_price"] = float(open_price)
        s["entry_date"] = pd.Timestamp(date).date().isoformat()
    elif (not desired) and position:
        entry = float(s["entry_price"])
        tr = float(open_price) / entry - 1 - 2 * FEE
        _record_trade(s, tr)
        s["position"] = False
        s["entry_price"] = None
        s["entry_date"] = None
    s["pending_date"] = None
    s["pending_signal"] = None


def _verification_label(s: dict) -> str:
    return "FROZEN_VERIFIED" if bool(s.get("frozen_verified")) else "LEGACY_LOCKED"


def _status_row(s: dict, now: str, update: str, marked: float | None = None) -> dict:
    trades = int(s.get("completed_trades", 0))
    wins = int(s.get("wins", 0))
    if marked is None:
        marked = float(s.get("realized_equity", 1.0))
    return {
        "시각UTC": now,
        "종목": s.get("종목", s.get("코드", "?")),
        "코드": s.get("코드", "?"),
        "시장": s.get("시장", "?"),
        "전략": s.get("전략", "?"),
        "동결검증": _verification_label(s),
        "신호기준일": s.get("last_signal_date") or s.get("registered_market_date") or "-",
        "종가신호": "인증상태변경" if update == "VERIFICATION_UPDATE" else "대기",
        "현재포지션": "LONG" if s.get("position") else "CASH",
        "진입일": s.get("entry_date") or "-",
        "관측거래일": int(s.get("observations", 0)),
        "완료거래": trades,
        "승률": wins / trades if trades else np.nan,
        "PF": _trade_pf(s),
        "전진누적수익": float(marked) - 1,
        "전진MDD": float(s.get("forward_mdd", 0.0)),
        "업데이트": update,
        "트래커": TRACKER_VERSION,
    }


def replay_unseen_bars(
    s: dict,
    raw: pd.DataFrame,
    live: pd.DataFrame,
    signals: pd.Series,
    dates: Iterable[pd.Timestamp],
    now: str,
) -> List[dict]:
    rows: List[dict] = []
    for date in [pd.Timestamp(x) for x in dates]:
        if date not in raw.index or date not in live.index:
            continue
        _execute_pending_at_open(s, float(raw.loc[date, "Open"]), date)
        close_price = float(raw.loc[date, "Close"])
        signal = bool(signals.loc[date])
        date_str = date.date().isoformat()
        s["pending_date"] = date_str
        s["pending_signal"] = signal
        s["last_signal_date"] = date_str
        s["observations"] = int(s.get("observations", 0)) + 1
        marked = mark_equity(s, close_price)
        peak = max(float(s.get("max_mark_equity", 1.0)), marked)
        s["max_mark_equity"] = peak
        dd = marked / peak - 1 if peak > 0 else 0.0
        s["forward_mdd"] = min(float(s.get("forward_mdd", 0.0)), dd)
        row = _status_row(s, now, "NEW_BAR", marked)
        row["신호기준일"] = date_str
        row["종가신호"] = "보유/진입" if signal else "현금/청산"
        rows.append(row)
    return rows


def _build_signal_series(ticker: str, market_code: str, s: dict) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    raw = dl(ticker, "2y")
    market = dl(market_code, "2y")
    live = make_live_features(raw, market)
    if live.empty:
        raise RuntimeError("no live features")
    kind = str(s["전략"])
    params = dict(s["전략파라미터"])
    if kind != "AI":
        return raw, live, build_rule_signal(live, kind, params).astype(bool)
    raw5 = dl(ticker, "5y")
    market5 = dl(market_code, "5y")
    train = make_features(raw5, market5, future=5, target_pct=.01)
    cutoff = pd.Timestamp(s.get("model_cutoff") or s.get("registered_market_date") or live.index[-1])
    train = train.loc[train.index <= cutoff]
    if len(train) < 500 or train["target"].nunique() < 2:
        raise RuntimeError("frozen AI training history unavailable")
    p = fit_ai_predict(train, live, True)
    probs = pd.Series(p, index=live.index)
    signals = (
        (probs >= float(params["threshold"]))
        & (live["Close"] > live["ema55"])
        & live["rsi"].between(45, 78)
    )
    return raw, live, signals.astype(bool)


def _new_state(row: pd.Series, latest_date: pd.Timestamp, now: str) -> dict:
    params = json.loads(str(row["전략파라미터"]))
    cutoff = str(row.get("1차데이터기준일", latest_date.date().isoformat()))
    return {
        "종목": str(row["종목"]),
        "코드": str(row["코드"]),
        "시장": str(row["시장"]),
        "전략": str(row["전략"]),
        "전략파라미터": params,
        "등록시각UTC": now,
        "registered_market_date": latest_date.date().isoformat(),
        "model_cutoff": cutoff,
        "admission_engine": None,
        "frozen_verified": False,
        "verification_time_utc": None,
        "verification_effective_after_date": None,
        "verification_revoked_after_date": None,
        "quarantine_reason": "awaiting frozen confirmation",
        "position": False,
        "entry_price": None,
        "entry_date": None,
        "pending_date": None,
        "pending_signal": None,
        "realized_equity": 1.0,
        "completed_trades": 0,
        "wins": 0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "trade_returns": [],
        "max_mark_equity": 1.0,
        "forward_mdd": 0.0,
        "observations": 0,
        "last_signal_date": None,
        "tracker_version": TRACKER_VERSION,
    }


def process_candidate(state: Dict[str, dict], row: pd.Series) -> List[dict]:
    ticker = str(row["코드"])
    market_name = str(row["시장"])
    market_code = "^KS11" if market_name == "KR" else "SPY"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if ticker not in state:
        raw = dl(ticker, "2y")
        market = dl(market_code, "2y")
        live = make_live_features(raw, market)
        if live.empty:
            raise RuntimeError("no live features")
        state[ticker] = _new_state(row, pd.Timestamp(live.index[-1]), now)
    s = state[ticker]
    s.setdefault("코드", ticker)
    s.setdefault("trade_returns", [])
    s.setdefault("registered_market_date", s.get("last_signal_date"))
    s.setdefault("model_cutoff", s.get("registered_market_date") or s.get("last_signal_date"))
    s.setdefault("frozen_verified", False)
    s.setdefault("quarantine_reason", "legacy admission awaiting frozen confirmation")
    s.setdefault("verification_effective_after_date", s.get("model_cutoff") if s.get("frozen_verified") else None)
    s.setdefault("verification_revoked_after_date", None)
    if s.get("frozen_verified") and not s.get("verification_effective_after_date"):
        s["verification_effective_after_date"] = s.get("model_cutoff") or s.get("registered_market_date")
    s["tracker_version"] = TRACKER_VERSION

    raw, live, signals = _build_signal_series(ticker, market_code, s)
    last = s.get("last_signal_date")
    if last is None:
        dates = [pd.Timestamp(live.index[-1])]
    else:
        last_ts = pd.Timestamp(last)
        dates = [pd.Timestamp(x) for x in live.index if pd.Timestamp(x) > last_ts]
    if dates:
        return replay_unseen_bars(s, raw, live, signals, dates, now)
    latest_date = pd.Timestamp(live.index[-1])
    latest_close = float(raw.loc[latest_date, "Close"])
    return [_status_row(s, now, "NO_NEW_BAR", mark_equity(s, latest_close))]


def _row_cutoff(row: pd.Series | None, fallback: str | None = None) -> str | None:
    if row is None:
        return fallback
    value = row.get("데이터기준일", fallback)
    if value is None or pd.isna(value):
        return fallback
    try:
        return pd.Timestamp(str(value)).date().isoformat()
    except Exception:
        return fallback


def reconcile_verifications(
    state: Dict[str, dict],
    primary: pd.DataFrame,
    confirmation: pd.DataFrame,
    now: str,
) -> List[dict]:
    """Reconcile current stage-2 status after all bars through its cutoff were replayed."""
    if primary.empty or "코드" not in primary.columns or "최종등급" not in primary.columns:
        return []
    if "엔진버전" in primary.columns and not primary["엔진버전"].astype(str).eq(EXPECTED_PRIMARY_ENGINE).all():
        return []

    primary_map = {str(r["코드"]): r for _, r in primary.iterrows()}
    confirm_map = (
        {str(r["코드"]): r for _, r in confirmation.iterrows()}
        if not confirmation.empty and "코드" in confirmation.columns
        else {}
    )
    global_cutoff = None
    if "데이터기준일" in primary.columns:
        vals = pd.to_datetime(primary["데이터기준일"], errors="coerce").dropna()
        if not vals.empty:
            global_cutoff = vals.max().date().isoformat()

    rows: List[dict] = []
    for ticker, s in state.items():
        before_verified = bool(s.get("frozen_verified"))
        before_reason = s.get("quarantine_reason")
        before_effective = s.get("verification_effective_after_date")
        before_revoked = s.get("verification_revoked_after_date")
        prow = primary_map.get(str(ticker))
        cutoff = _row_cutoff(prow, global_cutoff) if prow is not None else global_cutoff

        verified_now = False
        reason = None
        if prow is None:
            reason = "not present in current primary validation snapshot"
        elif str(prow.get("최종등급")) not in ELIGIBLE_PRIMARY_GRADES:
            reason = "no longer in current stage-2 candidate set"
        else:
            crow = confirm_map.get(str(ticker))
            if crow is None:
                reason = "current stage-2 confirmation missing"
            elif str(crow.get("확인엔진", "legacy")) != EXPECTED_CONFIRM_ENGINE:
                reason = "current stage-2 confirmation engine mismatch"
            elif str(crow.get("2차통과", "❌")) != "✅":
                reason = f"current stage-2 confirmation failed: {crow.get('보류사유', 'stage-2 failed')}"
            elif not admission_matches(s, crow):
                reason = "frozen confirmation parameters differ from admitted strategy"
            else:
                verified_now = True

        if verified_now:
            s["frozen_verified"] = True
            s["quarantine_reason"] = None
            s["admission_engine"] = EXPECTED_CONFIRM_ENGINE
            s["verification_revoked_after_date"] = None
            if not before_verified:
                s["verification_time_utc"] = now
                s["verification_effective_after_date"] = cutoff
            elif not s.get("verification_effective_after_date"):
                s["verification_effective_after_date"] = s.get("model_cutoff") or cutoff
        else:
            s["frozen_verified"] = False
            s["quarantine_reason"] = reason
            # Only a candidate that was actually verified can have a revocation
            # window in which earlier opens remain valid.
            if before_verified:
                s["verification_revoked_after_date"] = cutoff

        changed = (
            before_verified != bool(s.get("frozen_verified"))
            or before_reason != s.get("quarantine_reason")
            or before_effective != s.get("verification_effective_after_date")
            or before_revoked != s.get("verification_revoked_after_date")
        )
        if changed:
            rows.append(_status_row(s, now, "VERIFICATION_UPDATE"))
    return rows


def main():
    Path("reports").mkdir(exist_ok=True)
    state = load_state()
    old_log = load_log()
    primary = load_csv(PRIMARY)
    confirmation = load_csv(CONFIRM)
    rows: List[dict] = []

    # Current confirmed rows can introduce new candidates, but new admission is
    # not effective at the same day's open. Reconciliation happens after replay.
    if not confirmation.empty and {"2차통과", "코드"}.issubset(confirmation.columns):
        admitted = confirmation[
            (confirmation["2차통과"].astype(str) == "✅")
            & (
                confirmation.get("확인엔진", pd.Series("legacy", index=confirmation.index)).astype(str)
                == EXPECTED_CONFIRM_ENGINE
            )
        ]
        for _, row in admitted.iterrows():
            try:
                rows.extend(process_candidate(state, row))
            except Exception as e:
                rows.append({
                    "시각UTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "종목": row.get("종목", "?"),
                    "코드": row.get("코드", "?"),
                    "시장": row.get("시장", "?"),
                    "전략": row.get("전략", "?"),
                    "오류": repr(e),
                    "업데이트": "ERROR",
                    "트래커": TRACKER_VERSION,
                })

    touched = {str(r.get("코드")) for r in rows if r.get("코드")}
    for ticker, s in list(state.items()):
        if ticker in touched:
            continue
        pseudo = pd.Series({
            "종목": s["종목"],
            "코드": ticker,
            "시장": s["시장"],
            "전략": s["전략"],
            "전략파라미터": json.dumps(s["전략파라미터"], ensure_ascii=False),
        })
        try:
            rows.extend(process_candidate(state, pseudo))
        except Exception as e:
            rows.append({
                "시각UTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "종목": s.get("종목", "?"),
                "코드": ticker,
                "시장": s.get("시장", "?"),
                "전략": s.get("전략", "?"),
                "오류": repr(e),
                "업데이트": "ERROR",
                "트래커": TRACKER_VERSION,
            })

    reconcile_now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows.extend(reconcile_verifications(state, primary, confirmation, reconcile_now))

    save_state(state)
    new = pd.DataFrame(rows)
    combined = (
        pd.concat([old_log, new], ignore_index=True)
        if (not old_log.empty and not new.empty)
        else (new if not new.empty else old_log)
    )
    combined.to_csv(LOG_PATH, index=False, encoding="utf-8-sig")

    verified = sum(bool(s.get("frozen_verified")) for s in state.values())
    quarantined = len(state) - verified
    lines = [
        "# APEX forward-only paper tracker",
        "",
        f"- tracker: {TRACKER_VERSION}",
        f"- frozen candidates tracked: {len(state)}",
        f"- frozen-confirm verified: {verified}",
        f"- quarantined/locked: {quarantined}",
        f"- rows written this run: {len(new)}",
        "",
    ]
    if not new.empty:
        lines += ["## Latest", ""]
        for _, r in new.tail(30).iterrows():
            if pd.notna(r.get("오류")):
                lines.append(f"- ERROR {r.get('종목')} ({r.get('코드')}): {r.get('오류')}")
            else:
                lines.append(
                    f"- {r['종목']} ({r['코드']}): verify={r.get('동결검증')}, date={r['신호기준일']}, "
                    f"signal={r['종가신호']}, position={r['현재포지션']}, "
                    f"forward={float(r['전진누적수익']):.2%}, obs={int(r['관측거래일'])}, update={r['업데이트']}"
                )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
