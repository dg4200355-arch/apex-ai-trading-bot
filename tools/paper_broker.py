"""Autonomous shadow paper broker for APEX.

This module is downstream from validation. It NEVER sends live orders and its
results NEVER feed back into candidate promotion. It consumes only forward-tracker
events from FROZEN_VERIFIED candidates and maintains virtual cash, whole-share
positions, fees, slippage, correlation-cluster limits and account risk stops.

Execution model
---------------
- forward tracker decides at close t-1 and exposes resulting position at open t
- broker mirrors a position transition at that same open t
- buys use Open * (1 + slippage), sells use Open * (1 - slippage)
- no leverage, no shorting, no historical backfill before broker initialization
- one active position per correlation cluster
- at most three active positions per market account
- a 10% peak-to-equity drawdown permanently halts NEW buys; exits remain allowed
- broker P/L is research-only and does not affect validation gates
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import math
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from market_data import download_ohlcv

FORWARD = Path("reports/paper_forward.csv")
CANDIDATE_STATE = Path("reports/paper_state.json")
PORTFOLIO = Path("reports/portfolio_risk.csv")
BROKER_STATE = Path("reports/paper_broker_state.json")
ORDERS = Path("reports/paper_orders.csv")
ACCOUNT = Path("reports/paper_account.csv")
POSITIONS = Path("reports/paper_positions.csv")
SUMMARY = Path("reports/paper_broker.md")

VERSION = "paper-broker-1.1-risk-stop"
STATE_SCHEMA = 1
TRACKER_PREFIX = "paper-forward-1.2"
STARTING_CAPITAL = {
    "KR": {"currency": "KRW", "cash": 10_000_000.0},
    "US": {"currency": "USD", "cash": 10_000.0},
}
POSITION_FRACTION = 0.25
CASH_RESERVE_FRACTION = 0.10
MAX_POSITIONS_PER_MARKET = 3
HARD_DRAWDOWN_HALT = -0.10
FEE = 0.0015
SLIPPAGE = 0.0005

POSITION_COLUMNS = [
    "시장", "통화", "코드", "상관군집", "수량", "진입일", "평균진입가",
    "최근가격", "평가금액", "미실현손익", "브로커",
]


def _read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or not path.stat().st_size:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _append_csv(path: Path, new: pd.DataFrame):
    if new is None or new.empty:
        return
    old = _read_csv(path)
    out = pd.concat([old, new], ignore_index=True) if not old.empty else new
    out.to_csv(path, index=False, encoding="utf-8-sig")


def _ensure_account_schema(account: dict):
    initial = float(account.get("initial_cash", account.get("cash", 0.0)))
    account.setdefault("initial_cash", initial)
    account.setdefault("cash", initial)
    account.setdefault("peak_equity", initial)
    account.setdefault("last_equity", initial)
    account.setdefault("max_drawdown", 0.0)
    account.setdefault("risk_halt", False)
    account.setdefault("risk_halt_reason", None)
    account.setdefault("positions", {})
    account.setdefault("realized_pnl", 0.0)
    account.setdefault("completed_trades", 0)


def new_broker_state(now: str | None = None) -> dict:
    now = now or datetime.now(timezone.utc).isoformat(timespec="seconds")
    accounts = {}
    for market, cfg in STARTING_CAPITAL.items():
        cash = float(cfg["cash"])
        accounts[market] = {
            "currency": cfg["currency"],
            "initial_cash": cash,
            "cash": cash,
            "peak_equity": cash,
            "last_equity": cash,
            "max_drawdown": 0.0,
            "risk_halt": False,
            "risk_halt_reason": None,
            "positions": {},
            "realized_pnl": 0.0,
            "completed_trades": 0,
        }
    return {
        "schema": STATE_SCHEMA,
        "version": VERSION,
        "initialized_at_utc": now,
        "accounts": accounts,
        "ticker_last_event": {},
    }


def compute_buy_quantity(cash: float, equity: float, price: float) -> Tuple[int, float]:
    """Whole-share quantity with cash reserve and fixed maximum equity fraction."""
    if not all(np.isfinite([cash, equity, price])) or cash <= 0 or equity <= 0 or price <= 0:
        return 0, 0.0
    reserve = equity * CASH_RESERVE_FRACTION
    spendable = max(0.0, cash - reserve)
    budget = min(equity * POSITION_FRACTION, spendable)
    unit_cost = price * (1 + FEE)
    qty = int(math.floor(budget / unit_cost))
    return max(0, qty), budget


def cluster_is_free(account: dict, cluster: str, except_ticker: str | None = None) -> bool:
    for ticker, pos in account.get("positions", {}).items():
        if ticker == except_ticker:
            continue
        if str(pos.get("cluster")) == str(cluster):
            return False
    return True


def account_drawdown(account: dict) -> float:
    peak = float(account.get("peak_equity", 0.0))
    equity = float(account.get("last_equity", 0.0))
    if peak <= 0:
        return 0.0
    return equity / peak - 1


def update_account_risk(account: dict) -> float:
    """Update worst drawdown and permanently halt new entries at hard threshold."""
    _ensure_account_schema(account)
    dd = account_drawdown(account)
    account["max_drawdown"] = min(float(account.get("max_drawdown", 0.0)), dd)
    if dd <= HARD_DRAWDOWN_HALT:
        account["risk_halt"] = True
        account["risk_halt_reason"] = f"DRAWDOWN_{HARD_DRAWDOWN_HALT:.0%}"
    return dd


def execute_buy(account: dict, ticker: str, market: str, cluster: str, open_price: float, date: str):
    _ensure_account_schema(account)
    if bool(account.get("risk_halt")):
        return None, "ACCOUNT_DRAWDOWN_HALT"
    exec_price = float(open_price) * (1 + SLIPPAGE)
    equity = float(account.get("last_equity", account.get("cash", 0.0)))
    cash = float(account.get("cash", 0.0))
    qty, _ = compute_buy_quantity(cash, equity, exec_price)
    if qty < 1:
        return None, "INSUFFICIENT_CASH"
    notional = qty * exec_price
    fee = notional * FEE
    total = notional + fee
    if total > cash + 1e-9:
        return None, "INSUFFICIENT_CASH"
    account["cash"] = cash - total
    account.setdefault("positions", {})[ticker] = {
        "ticker": ticker,
        "market": market,
        "cluster": cluster,
        "qty": qty,
        "entry_price": exec_price,
        "entry_fee": fee,
        "cost_total": total,
        "entry_date": date,
        "last_price": exec_price,
    }
    return {
        "qty": qty, "price": exec_price, "fee": fee,
        "realized_pnl": 0.0, "cash_after": account["cash"],
    }, None


def execute_sell(account: dict, ticker: str, open_price: float):
    _ensure_account_schema(account)
    pos = account.get("positions", {}).get(ticker)
    if not pos:
        return None, "NO_POSITION"
    qty = int(pos["qty"])
    exec_price = float(open_price) * (1 - SLIPPAGE)
    gross = qty * exec_price
    fee = gross * FEE
    net = gross - fee
    realized = net - float(pos.get("cost_total", 0.0))
    account["cash"] = float(account.get("cash", 0.0)) + net
    account["realized_pnl"] = float(account.get("realized_pnl", 0.0)) + realized
    account["completed_trades"] = int(account.get("completed_trades", 0)) + 1
    del account["positions"][ticker]
    return {
        "qty": qty, "price": exec_price, "fee": fee,
        "realized_pnl": realized, "cash_after": account["cash"],
    }, None


def _price_frame(cache: Dict[str, pd.DataFrame], ticker: str) -> pd.DataFrame:
    if ticker not in cache:
        cache[ticker] = download_ohlcv(ticker, period="2y")
    return cache[ticker]


def price_on(cache: Dict[str, pd.DataFrame], ticker: str, date: str, field: str) -> float:
    d = _price_frame(cache, ticker)
    ts = pd.Timestamp(date)
    if ts not in d.index:
        raise KeyError(f"no {field} for {ticker} on {date}")
    value = float(d.loc[ts, field])
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"bad {field} for {ticker} on {date}")
    return value


def mark_account(account: dict, cache: Dict[str, pd.DataFrame], date: str, field: str = "Close") -> Tuple[float, float]:
    _ensure_account_schema(account)
    market_value = 0.0
    for ticker, pos in account.get("positions", {}).items():
        try:
            px = price_on(cache, ticker, date, field)
            pos["last_price"] = px
        except Exception:
            px = float(pos.get("last_price", pos.get("entry_price", 0.0)))
        market_value += int(pos.get("qty", 0)) * px
    equity = float(account.get("cash", 0.0)) + market_value
    account["last_equity"] = equity
    account["peak_equity"] = max(float(account.get("peak_equity", equity)), equity)
    update_account_risk(account)
    return equity, market_value


def _load_cluster_map() -> Dict[str, str]:
    df = _read_csv(PORTFOLIO)
    if df.empty or "코드" not in df.columns:
        return {}
    return {str(r["코드"]): str(r.get("상관군집", r["코드"])) for _, r in df.iterrows()}


def _load_candidate_state() -> Dict[str, dict]:
    obj = _read_json(CANDIDATE_STATE, {})
    return obj if isinstance(obj, dict) else {}


def _valid_forward_events() -> pd.DataFrame:
    df = _read_csv(FORWARD)
    if df.empty:
        return df
    required = {"코드", "시장", "신호기준일", "현재포지션", "업데이트", "트래커"}
    if not required.issubset(df.columns):
        return pd.DataFrame()
    mask = df["업데이트"].astype(str).eq("NEW_BAR")
    mask &= df["트래커"].astype(str).str.startswith(TRACKER_PREFIX)
    if "동결검증" in df.columns:
        mask &= df["동결검증"].astype(str).eq("FROZEN_VERIFIED")
    out = df.loc[mask].copy()
    if out.empty:
        return out
    out["신호기준일"] = pd.to_datetime(out["신호기준일"], errors="coerce")
    out = out.dropna(subset=["신호기준일"])
    out["날짜"] = out["신호기준일"].dt.date.astype(str)
    return out.sort_values(["날짜", "시장", "코드"]).drop_duplicates(["코드", "날짜"], keep="last")


def _initialize_event_watermarks(state: dict, candidate_state: Dict[str, dict]):
    marks = state.setdefault("ticker_last_event", {})
    for ticker, s in candidate_state.items():
        if ticker not in marks and s.get("last_signal_date"):
            marks[ticker] = str(s["last_signal_date"])


def _order_row(now: str, date: str, market: str, ticker: str, side: str, status: str,
               reason: str, cluster: str, qty=0, price=np.nan, fee=0.0,
               realized_pnl=0.0, cash_after=np.nan):
    return {
        "시각UTC": now, "체결일": date, "시장": market, "코드": ticker,
        "구분": side, "상태": status, "사유": reason, "상관군집": cluster,
        "수량": qty, "체결가": price, "수수료": fee, "슬리피지": SLIPPAGE,
        "실현손익": realized_pnl, "체결후현금": cash_after, "브로커": VERSION,
    }


def process_events(state: dict, events: pd.DataFrame, candidate_state: Dict[str, dict], cluster_map: Dict[str, str]):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cache: Dict[str, pd.DataFrame] = {}
    order_rows: List[dict] = []
    account_rows: List[dict] = []
    marks = state.setdefault("ticker_last_event", {})

    if events.empty:
        return order_rows, account_rows

    unseen = []
    for _, row in events.iterrows():
        ticker = str(row["코드"])
        date = str(row["날짜"])
        last = marks.get(ticker)
        if last is None or pd.Timestamp(date) > pd.Timestamp(last):
            unseen.append(row)
    if not unseen:
        return order_rows, account_rows
    work = pd.DataFrame(unseen).sort_values(["날짜", "시장", "코드"])

    for (date, market), group in work.groupby(["날짜", "시장"], sort=True):
        market = str(market)
        if market not in state["accounts"]:
            continue
        account = state["accounts"][market]
        _ensure_account_schema(account)
        failed_tickers = set()

        # Mark at the open before any new entries. Existing positions may trigger
        # the permanent account drawdown kill switch. Exits remain allowed.
        mark_account(account, cache, date, "Open")

        # Sells first so exits release cash and cluster capacity.
        for _, row in group.iterrows():
            ticker = str(row["코드"])
            desired_long = str(row["현재포지션"]).upper() == "LONG"
            if ticker in account.get("positions", {}) and not desired_long:
                cluster = str(account["positions"][ticker].get("cluster", cluster_map.get(ticker, ticker)))
                try:
                    open_px = price_on(cache, ticker, date, "Open")
                    fill, err = execute_sell(account, ticker, open_px)
                    if fill:
                        order_rows.append(_order_row(now, date, market, ticker, "SELL", "FILLED", "SIGNAL_EXIT", cluster, **fill))
                    else:
                        order_rows.append(_order_row(now, date, market, ticker, "SELL", "BLOCKED", err or "SELL_ERROR", cluster))
                except Exception as e:
                    failed_tickers.add(ticker)
                    order_rows.append(_order_row(now, date, market, ticker, "SELL", "ERROR", repr(e), cluster))

        # Entries: earliest frozen admission wins same-day ties inside one cluster.
        entries = []
        for _, row in group.iterrows():
            ticker = str(row["코드"])
            desired_long = str(row["현재포지션"]).upper() == "LONG"
            if not desired_long or ticker in account.get("positions", {}):
                continue
            cs = candidate_state.get(ticker, {})
            entries.append((str(cs.get("등록시각UTC", "9999")), ticker))
        entries.sort(key=lambda x: (x[0], x[1]))

        for _, ticker in entries:
            cluster = str(cluster_map.get(ticker, ticker))
            cs = candidate_state.get(ticker, {})
            verified = bool(cs.get("frozen_verified")) and not cs.get("quarantine_reason")
            if not verified:
                order_rows.append(_order_row(now, date, market, ticker, "BUY", "BLOCKED", "NOT_FROZEN_VERIFIED", cluster))
                continue
            if bool(account.get("risk_halt")):
                order_rows.append(_order_row(now, date, market, ticker, "BUY", "BLOCKED", "ACCOUNT_DRAWDOWN_HALT", cluster))
                continue
            if len(account.get("positions", {})) >= MAX_POSITIONS_PER_MARKET:
                order_rows.append(_order_row(now, date, market, ticker, "BUY", "BLOCKED", "MAX_POSITIONS", cluster))
                continue
            if not cluster_is_free(account, cluster):
                order_rows.append(_order_row(now, date, market, ticker, "BUY", "BLOCKED", "CLUSTER_OCCUPIED", cluster))
                continue
            try:
                open_px = price_on(cache, ticker, date, "Open")
                fill, err = execute_buy(account, ticker, market, cluster, open_px, date)
                if fill:
                    order_rows.append(_order_row(now, date, market, ticker, "BUY", "FILLED", "SIGNAL_ENTRY", cluster, **fill))
                else:
                    order_rows.append(_order_row(now, date, market, ticker, "BUY", "BLOCKED", err or "BUY_ERROR", cluster))
            except Exception as e:
                failed_tickers.add(ticker)
                order_rows.append(_order_row(now, date, market, ticker, "BUY", "ERROR", repr(e), cluster))

        equity, market_value = mark_account(account, cache, date, "Close")
        initial = float(account.get("initial_cash", equity))
        account_rows.append({
            "시각UTC": now, "기준일": date, "시장": market, "통화": account["currency"],
            "현금": float(account["cash"]), "보유평가": market_value, "총자산": equity,
            "누적수익률": equity / initial - 1 if initial > 0 else np.nan,
            "최대낙폭": float(account.get("max_drawdown", 0.0)),
            "현재낙폭": account_drawdown(account),
            "신규매수중지": "⛔" if account.get("risk_halt") else "-",
            "보유종목수": len(account.get("positions", {})),
            "완료거래": int(account.get("completed_trades", 0)),
            "실현손익": float(account.get("realized_pnl", 0.0)), "브로커": VERSION,
        })

        # A transient price/data ERROR must be retried on the next workflow run.
        # Intentionally blocked events are consumed and can be reconsidered on the
        # following NEW_BAR if the tracker remains LONG.
        for _, row in group.iterrows():
            ticker = str(row["코드"])
            if ticker not in failed_tickers:
                marks[ticker] = str(date)

    return order_rows, account_rows


def current_positions_frame(state: dict) -> pd.DataFrame:
    rows = []
    for market, account in state.get("accounts", {}).items():
        _ensure_account_schema(account)
        for ticker, pos in account.get("positions", {}).items():
            qty = int(pos.get("qty", 0))
            last = float(pos.get("last_price", pos.get("entry_price", np.nan)))
            entry = float(pos.get("entry_price", np.nan))
            unreal = qty * (last - entry) - float(pos.get("entry_fee", 0.0)) if np.isfinite(last) and np.isfinite(entry) else np.nan
            rows.append({
                "시장": market, "통화": account.get("currency"), "코드": ticker,
                "상관군집": pos.get("cluster", ticker), "수량": qty,
                "진입일": pos.get("entry_date", "-"), "평균진입가": entry,
                "최근가격": last, "평가금액": qty * last if np.isfinite(last) else np.nan,
                "미실현손익": unreal, "브로커": VERSION,
            })
    return pd.DataFrame(rows, columns=POSITION_COLUMNS)


def initial_account_rows(state: dict, candidate_state: Dict[str, dict]) -> pd.DataFrame:
    dates = [str(s.get("last_signal_date")) for s in candidate_state.values() if s.get("last_signal_date")]
    date = max(dates) if dates else "-"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    for market, a in state.get("accounts", {}).items():
        _ensure_account_schema(a)
        initial = float(a["initial_cash"])
        rows.append({
            "시각UTC": now, "기준일": date, "시장": market, "통화": a["currency"],
            "현금": initial, "보유평가": 0.0, "총자산": initial, "누적수익률": 0.0,
            "최대낙폭": 0.0, "현재낙폭": 0.0, "신규매수중지": "-",
            "보유종목수": 0, "완료거래": 0, "실현손익": 0.0,
            "브로커": VERSION,
        })
    return pd.DataFrame(rows)


def write_summary(state: dict, orders_run: List[dict]):
    lines = [
        "# APEX autonomous shadow paper broker", "",
        f"- broker: {VERSION}",
        "- live orders: NEVER",
        f"- position sizing: {POSITION_FRACTION:.0%} max per entry",
        f"- cash reserve: {CASH_RESERVE_FRACTION:.0%}",
        f"- max positions per market: {MAX_POSITIONS_PER_MARKET}",
        f"- hard new-entry halt: {HARD_DRAWDOWN_HALT:.0%} from account peak",
        f"- fee/slippage each side: {FEE:.2%} / {SLIPPAGE:.2%}",
        "- candidate promotion is independent from broker P/L", "",
        "## Accounts", "",
    ]
    for market, a in state.get("accounts", {}).items():
        _ensure_account_schema(a)
        initial = float(a.get("initial_cash", 1.0))
        equity = float(a.get("last_equity", initial))
        lines.append(
            f"- {market} {a.get('currency')}: equity={equity:,.2f}, cash={float(a.get('cash',0)):,.2f}, "
            f"return={equity/initial-1:.2%}, max_dd={float(a.get('max_drawdown',0)):.2%}, "
            f"halt={bool(a.get('risk_halt'))}, positions={len(a.get('positions',{}))}, trades={int(a.get('completed_trades',0))}"
        )
    lines += ["", "## This run", "", f"- order events: {len(orders_run)}"]
    for r in orders_run[-20:]:
        lines.append(f"- {r['체결일']} {r['시장']} {r['코드']} {r['구분']} {r['상태']} {r['사유']}")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    Path("reports").mkdir(exist_ok=True)
    candidate_state = _load_candidate_state()
    cluster_map = _load_cluster_map()
    events = _valid_forward_events()
    state = _read_json(BROKER_STATE, None)

    if not isinstance(state, dict) or int(state.get("schema", -1)) != STATE_SCHEMA:
        state = new_broker_state()
        _initialize_event_watermarks(state, candidate_state)
        BROKER_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        current_positions_frame(state).to_csv(POSITIONS, index=False, encoding="utf-8-sig")
        initial_account_rows(state, candidate_state).to_csv(ACCOUNT, index=False, encoding="utf-8-sig")
        write_summary(state, [])
        print("paper broker initialized; no historical backfill")
        return

    state["version"] = VERSION
    for account in state.get("accounts", {}).values():
        _ensure_account_schema(account)
    orders_run, account_rows = process_events(state, events, candidate_state, cluster_map)
    BROKER_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    _append_csv(ORDERS, pd.DataFrame(orders_run))
    _append_csv(ACCOUNT, pd.DataFrame(account_rows))
    current_positions_frame(state).to_csv(POSITIONS, index=False, encoding="utf-8-sig")
    write_summary(state, orders_run)
    print(SUMMARY.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
