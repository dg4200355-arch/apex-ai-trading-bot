"""Forward-only paper tracker with immutable admission verification.

Once admitted, strategy family and parameters are frozen. Future runs process
EVERY unseen completed market bar in chronological order. Legacy candidates keep
their forward history, but they cannot be promoted until the current frozen stage-2
engine re-confirms the exact same strategy family and exact same parameters.

For AI candidates, the model training cutoff is frozen at admission. No live orders
are placed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from engine import atr, build_rule_signal, ema, fit_ai_predict, make_features, rsi

CONFIRM = Path("reports/latest_confirmation.csv")
STATE_PATH = Path("reports/paper_state.json")
LOG_PATH = Path("reports/paper_forward.csv")
SUMMARY_PATH = Path("reports/paper_forward.md")
FEE = 0.0015
TRACKER_VERSION = "paper-forward-1.2-frozen-admission"
EXPECTED_CONFIRM_ENGINE = "8.5-frozen-confirm"


def dl(ticker: str, period: str = "2y") -> pd.DataFrame:
    d = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
    if d is None or d.empty:
        raise RuntimeError(f"no data: {ticker}")
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    need = ["Open", "High", "Low", "Close", "Volume"]
    if any(c not in d.columns for c in need):
        raise RuntimeError(f"bad OHLCV: {ticker}")
    return d[need].dropna().sort_index()


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


def normalized_params(obj) -> str:
    if isinstance(obj, str):
        obj = json.loads(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def admission_matches(state_row: dict, confirmation_row: pd.Series) -> bool:
    try:
        return (
            str(state_row.get("전략")) == str(confirmation_row["전략"])
            and normalized_params(state_row.get("전략파라미터", {})) == normalized_params(str(confirmation_row["전략파라미터"]))
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

        trades = int(s.get("completed_trades", 0))
        wins = int(s.get("wins", 0))
        rows.append({
            "시각UTC": now,
            "종목": s.get("종목", "?"),
            "코드": s.get("코드", "?"),
            "시장": s.get("시장", "?"),
            "전략": s.get("전략", "?"),
            "동결검증": _verification_label(s),
            "신호기준일": date_str,
            "종가신호": "보유/진입" if signal else "현금/청산",
            "현재포지션": "LONG" if s.get("position") else "CASH",
            "진입일": s.get("entry_date") or "-",
            "관측거래일": int(s.get("observations", 0)),
            "완료거래": trades,
            "승률": wins / trades if trades else np.nan,
            "PF": _trade_pf(s),
            "전진누적수익": marked - 1,
            "전진MDD": float(s.get("forward_mdd", 0.0)),
            "업데이트": "NEW_BAR",
            "트래커": TRACKER_VERSION,
        })
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
        signals = build_rule_signal(live, kind, params).astype(bool)
        return raw, live, signals

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
    confirm_engine = str(row.get("확인엔진", "legacy"))
    verified = confirm_engine == EXPECTED_CONFIRM_ENGINE
    return {
        "종목": str(row["종목"]),
        "코드": str(row["코드"]),
        "시장": str(row["시장"]),
        "전략": str(row["전략"]),
        "전략파라미터": params,
        "등록시각UTC": now,
        "registered_market_date": latest_date.date().isoformat(),
        "model_cutoff": str(row.get("1차데이터기준일", latest_date.date().isoformat())),
        "admission_engine": confirm_engine,
        "frozen_verified": verified,
        "verification_time_utc": now if verified else None,
        "quarantine_reason": None if verified else "awaiting frozen confirmation",
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


def _refresh_admission_verification(s: dict, row: pd.Series, now: str):
    engine = str(row.get("확인엔진", "legacy"))
    if engine != EXPECTED_CONFIRM_ENGINE:
        return
    if admission_matches(s, row):
        s["frozen_verified"] = True
        s["verification_time_utc"] = now
        s["admission_engine"] = engine
        s["quarantine_reason"] = None
    else:
        s["frozen_verified"] = False
        s["quarantine_reason"] = "frozen confirmation parameters differ from admitted strategy"


def process_candidate(state: Dict[str, dict], row: pd.Series, current_confirmation: bool = False) -> List[dict]:
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
        latest_date = pd.Timestamp(live.index[-1])
        state[ticker] = _new_state(row, latest_date, now)

    s = state[ticker]
    s.setdefault("코드", ticker)
    s.setdefault("trade_returns", [])
    s.setdefault("registered_market_date", s.get("last_signal_date"))
    s.setdefault("model_cutoff", s.get("registered_market_date") or s.get("last_signal_date"))
    s.setdefault("frozen_verified", False)
    s.setdefault("quarantine_reason", "legacy admission awaiting frozen confirmation")
    s["tracker_version"] = TRACKER_VERSION
    if current_confirmation:
        _refresh_admission_verification(s, row, now)

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
    marked = mark_equity(s, latest_close)
    trades = int(s.get("completed_trades", 0))
    wins = int(s.get("wins", 0))
    return [{
        "시각UTC": now,
        "종목": s.get("종목", ticker),
        "코드": ticker,
        "시장": s.get("시장", market_name),
        "전략": s.get("전략", "?"),
        "동결검증": _verification_label(s),
        "신호기준일": s.get("last_signal_date") or latest_date.date().isoformat(),
        "종가신호": "대기",
        "현재포지션": "LONG" if s.get("position") else "CASH",
        "진입일": s.get("entry_date") or "-",
        "관측거래일": int(s.get("observations", 0)),
        "완료거래": trades,
        "승률": wins / trades if trades else np.nan,
        "PF": _trade_pf(s),
        "전진누적수익": marked - 1,
        "전진MDD": float(s.get("forward_mdd", 0.0)),
        "업데이트": "NO_NEW_BAR",
        "트래커": TRACKER_VERSION,
    }]


def main():
    Path("reports").mkdir(exist_ok=True)
    state = load_state()
    old_log = load_log()
    rows: List[dict] = []

    if CONFIRM.exists():
        try:
            confirmation = pd.read_csv(CONFIRM)
        except Exception:
            confirmation = pd.DataFrame()
    else:
        confirmation = pd.DataFrame()

    if not confirmation.empty and "2차통과" in confirmation.columns:
        admitted = confirmation[confirmation["2차통과"] == "✅"]
        for _, row in admitted.iterrows():
            try:
                rows.extend(process_candidate(state, row, current_confirmation=True))
            except Exception as e:
                rows.append({
                    "시각UTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "종목": row.get("종목", "?"), "코드": row.get("코드", "?"),
                    "시장": row.get("시장", "?"), "전략": row.get("전략", "?"),
                    "오류": repr(e), "업데이트": "ERROR", "트래커": TRACKER_VERSION,
                })

    touched = {str(r.get("코드")) for r in rows if r.get("코드")}
    for ticker, s in list(state.items()):
        if ticker in touched:
            continue
        pseudo = pd.Series({
            "종목": s["종목"], "코드": ticker, "시장": s["시장"], "전략": s["전략"],
            "전략파라미터": json.dumps(s["전략파라미터"], ensure_ascii=False),
        })
        try:
            rows.extend(process_candidate(state, pseudo, current_confirmation=False))
        except Exception as e:
            rows.append({
                "시각UTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "종목": s.get("종목", "?"), "코드": ticker, "시장": s.get("시장", "?"),
                "전략": s.get("전략", "?"), "오류": repr(e),
                "업데이트": "ERROR", "트래커": TRACKER_VERSION,
            })

    save_state(state)
    new = pd.DataFrame(rows)
    combined = pd.concat([old_log, new], ignore_index=True) if (not old_log.empty and not new.empty) else (new if not new.empty else old_log)
    combined.to_csv(LOG_PATH, index=False, encoding="utf-8-sig")

    verified = sum(bool(s.get("frozen_verified")) for s in state.values())
    lines = [
        "# APEX forward-only paper tracker", "",
        f"- tracker: {TRACKER_VERSION}",
        f"- frozen candidates tracked: {len(state)}",
        f"- frozen-confirm verified: {verified}",
        f"- rows written this run: {len(new)}", "",
    ]
    if not new.empty:
        lines += ["## Latest", ""]
        for _, r in new.tail(20).iterrows():
            if pd.notna(r.get("오류")):
                lines.append(f"- ERROR {r.get('종목')} ({r.get('코드')}): {r.get('오류')}")
            else:
                lines.append(
                    f"- {r['종목']} ({r['코드']}): verify={r.get('동결검증')}, date={r['신호기준일']}, "
                    f"signal={r['종가신호']}, position={r['현재포지션']}, forward={float(r['전진누적수익']):.2%}, "
                    f"obs={int(r['관측거래일'])}, update={r['업데이트']}"
                )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
