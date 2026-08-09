"""Forward-only paper tracker for candidates that pass second-stage confirmation.

Once a candidate is admitted, its strategy family and parameters are frozen in
paper_state.json. Future runs only process NEW market bars. Signals are decided
at a completed close and changes are executed at the next available open.
This is deliberately separate from the backtest/ranking loop to avoid reselecting
history after seeing new outcomes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Dict

import numpy as np
import pandas as pd
import yfinance as yf

from engine import FEATURES, atr, build_rule_signal, ema, fit_ai_predict, make_features, rsi

CONFIRM = Path("reports/latest_confirmation.csv")
STATE_PATH = Path("reports/paper_state.json")
LOG_PATH = Path("reports/paper_forward.csv")
SUMMARY_PATH = Path("reports/paper_forward.md")
FEE = 0.0015
TRACKER_VERSION = "paper-forward-1.0"


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
    """Feature frame with no future target, so the newest completed bar is usable."""
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


def latest_signal(ticker: str, market_code: str, kind: str, params: dict) -> tuple[pd.Timestamp, bool, float, pd.DataFrame]:
    raw = dl(ticker, "2y")
    market = dl(market_code, "2y")
    live = make_live_features(raw, market)
    if live.empty:
        raise RuntimeError("no live features")
    latest = live.iloc[[-1]].copy()
    latest_date = pd.Timestamp(latest.index[-1])

    if kind == "AI":
        raw5 = dl(ticker, "5y")
        market5 = dl(market_code, "5y")
        train = make_features(raw5, market5, future=5, target_pct=.01)
        if len(train) < 500 or train["target"].nunique() < 2:
            raise RuntimeError("AI training history unavailable")
        p = float(fit_ai_predict(train, latest, True)[0])
        signal = bool(
            p >= float(params["threshold"])
            and float(latest["Close"].iloc[0]) > float(latest["ema55"].iloc[0])
            and 45 <= float(latest["rsi"].iloc[0]) <= 78
        )
    else:
        full_sig = build_rule_signal(live, kind, params)
        signal = bool(full_sig.iloc[-1])

    return latest_date, signal, float(latest["Close"].iloc[0]), raw


def next_open_after(raw: pd.DataFrame, date_str: str):
    d = pd.Timestamp(date_str)
    later = raw.loc[raw.index > d]
    if later.empty:
        return None
    idx = pd.Timestamp(later.index[0])
    return idx, float(later["Open"].iloc[0])


def mark_equity(s: dict, close_price: float) -> float:
    realized = float(s.get("realized_equity", 1.0))
    if bool(s.get("position")) and s.get("entry_price"):
        gross = close_price / float(s["entry_price"]) - 1
        # include both estimated sides so current mark is conservative
        return realized * (1 + gross - 2 * FEE)
    return realized


def process_candidate(state: Dict[str, dict], row: pd.Series) -> dict:
    ticker = str(row["코드"])
    kind = str(row["전략"])
    params = json.loads(str(row["전략파라미터"]))
    market = str(row["시장"])
    market_code = "^KS11" if market == "KR" else "SPY"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if ticker not in state:
        state[ticker] = {
            "종목": str(row["종목"]),
            "코드": ticker,
            "시장": market,
            "전략": kind,
            "전략파라미터": params,
            "등록시각UTC": now,
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
            "max_mark_equity": 1.0,
            "forward_mdd": 0.0,
            "observations": 0,
            "last_signal_date": None,
            "tracker_version": TRACKER_VERSION,
        }

    s = state[ticker]
    # Never mutate the frozen strategy after admission.
    kind = str(s["전략"])
    params = dict(s["전략파라미터"])
    latest_date, signal, latest_close, raw = latest_signal(ticker, market_code, kind, params)

    # Execute the PRIOR close decision only when the following market open is present.
    if s.get("pending_date") is not None:
        nxt = next_open_after(raw, str(s["pending_date"]))
        if nxt is not None:
            exec_date, exec_price = nxt
            desired = bool(s.get("pending_signal"))
            position = bool(s.get("position"))
            if desired and not position:
                s["position"] = True
                s["entry_price"] = exec_price
                s["entry_date"] = exec_date.date().isoformat()
            elif (not desired) and position:
                entry = float(s["entry_price"])
                tr = exec_price / entry - 1 - 2 * FEE
                s["realized_equity"] = float(s.get("realized_equity", 1.0)) * (1 + tr)
                s["completed_trades"] = int(s.get("completed_trades", 0)) + 1
                if tr > 0:
                    s["wins"] = int(s.get("wins", 0)) + 1
                    s["gross_profit"] = float(s.get("gross_profit", 0.0)) + tr
                else:
                    s["gross_loss"] = float(s.get("gross_loss", 0.0)) + abs(tr)
                s["position"] = False
                s["entry_price"] = None
                s["entry_date"] = None
            s["pending_date"] = None
            s["pending_signal"] = None

    date_str = latest_date.date().isoformat()
    if s.get("last_signal_date") != date_str:
        s["pending_date"] = date_str
        s["pending_signal"] = bool(signal)
        s["last_signal_date"] = date_str
        s["observations"] = int(s.get("observations", 0)) + 1

    marked = mark_equity(s, latest_close)
    peak = max(float(s.get("max_mark_equity", 1.0)), marked)
    s["max_mark_equity"] = peak
    dd = marked / peak - 1 if peak > 0 else 0.0
    s["forward_mdd"] = min(float(s.get("forward_mdd", 0.0)), dd)
    trades = int(s.get("completed_trades", 0))
    wins = int(s.get("wins", 0))
    gp = float(s.get("gross_profit", 0.0))
    gl = float(s.get("gross_loss", 0.0))
    pf = gp / gl if gl > 0 else np.nan

    return {
        "시각UTC": now,
        "종목": s["종목"],
        "코드": ticker,
        "시장": market,
        "전략": kind,
        "신호기준일": date_str,
        "종가신호": "보유/진입" if signal else "현금/청산",
        "현재포지션": "LONG" if s.get("position") else "CASH",
        "진입일": s.get("entry_date") or "-",
        "관측거래일": int(s.get("observations", 0)),
        "완료거래": trades,
        "승률": wins / trades if trades else np.nan,
        "PF": pf,
        "전진누적수익": marked - 1,
        "전진MDD": float(s.get("forward_mdd", 0.0)),
        "트래커": TRACKER_VERSION,
    }


def main():
    Path("reports").mkdir(exist_ok=True)
    state = load_state()
    old_log = load_log()
    rows = []

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
                rows.append(process_candidate(state, row))
            except Exception as e:
                rows.append({
                    "시각UTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "종목": row.get("종목", "?"), "코드": row.get("코드", "?"),
                    "시장": row.get("시장", "?"), "전략": row.get("전략", "?"),
                    "오류": repr(e), "트래커": TRACKER_VERSION,
                })

    # Continue tracking previously admitted candidates even if they are not in today's scan.
    current_codes = {str(r.get("코드")) for r in rows if r.get("코드")}
    for ticker, s in list(state.items()):
        if ticker in current_codes:
            continue
        pseudo = pd.Series({
            "종목": s["종목"], "코드": ticker, "시장": s["시장"], "전략": s["전략"],
            "전략파라미터": json.dumps(s["전략파라미터"], ensure_ascii=False),
        })
        try:
            rows.append(process_candidate(state, pseudo))
        except Exception as e:
            rows.append({
                "시각UTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "종목": s.get("종목", "?"), "코드": ticker, "시장": s.get("시장", "?"),
                "전략": s.get("전략", "?"), "오류": repr(e), "트래커": TRACKER_VERSION,
            })

    save_state(state)
    new = pd.DataFrame(rows)
    if not new.empty:
        combined = pd.concat([old_log, new], ignore_index=True) if not old_log.empty else new
    else:
        combined = old_log
    combined.to_csv(LOG_PATH, index=False, encoding="utf-8-sig")

    latest = new.copy()
    lines = [
        "# APEX forward-only paper tracker", "",
        f"- tracker: {TRACKER_VERSION}",
        f"- frozen candidates tracked: {len(state)}",
        f"- rows updated this run: {len(new)}", "",
    ]
    if not latest.empty:
        lines += ["## Latest", ""]
        for _, r in latest.iterrows():
            if "오류" in r and pd.notna(r.get("오류")):
                lines.append(f"- ERROR {r.get('종목')} ({r.get('코드')}): {r.get('오류')}")
            else:
                lines.append(
                    f"- {r['종목']} ({r['코드']}): signal={r['종가신호']}, position={r['현재포지션']}, "
                    f"forward={r['전진누적수익']:.2%}, trades={int(r['완료거래'])}"
                )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
