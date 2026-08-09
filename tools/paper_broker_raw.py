"""Raw-execution autonomous shadow broker for APEX.

Research signals come from adjusted data upstream, but persistent virtual fills and
account valuation use raw unadjusted market prices. Corporate actions are applied
before the event-date open: cash dividends are credited to pre-existing holders and
integer-safe stock splits adjust quantity/cost basis. No live orders are ever sent.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from market_data import download_trade_actions, download_trade_ohlcv
from tools import paper_broker as pb

VERSION = "paper-broker-1.4-raw-execution"
PRICE_BASIS = "RAW_EXECUTION"
STATE_SCHEMA = pb.STATE_SCHEMA

# Keep legacy pure accounting helpers on the new report version.
pb.VERSION = VERSION


def _raw_frame(cache: Dict[str, pd.DataFrame], ticker: str) -> pd.DataFrame:
    if ticker not in cache:
        d = download_trade_ohlcv(ticker, period="2y")
        if d.attrs.get("price_basis") != PRICE_BASIS:
            raise RuntimeError(f"unexpected execution price basis: {ticker}")
        cache[ticker] = d
    return cache[ticker]


def raw_price_on(cache: Dict[str, pd.DataFrame], ticker: str, date: str, field: str) -> float:
    d = _raw_frame(cache, ticker)
    ts = pd.Timestamp(date)
    if ts not in d.index:
        raise KeyError(f"no raw {field} for {ticker} on {date}")
    value = float(d.loc[ts, field])
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"bad raw {field} for {ticker} on {date}")
    return value


def _action_frame(cache: Dict[str, pd.DataFrame], ticker: str) -> pd.DataFrame:
    if ticker not in cache:
        cache[ticker] = download_trade_actions(ticker, period="2y")
    return cache[ticker]


def _action_values(cache: Dict[str, pd.DataFrame], ticker: str, date: str) -> Tuple[float, float]:
    d = _action_frame(cache, ticker)
    ts = pd.Timestamp(date)
    if ts not in d.index:
        return 0.0, 0.0
    return float(d.loc[ts, "Dividends"]), float(d.loc[ts, "Stock Splits"])


def migrate_state_to_raw(state: dict) -> bool:
    """Return True when a flat legacy account is migrated to immutable raw fills."""
    if not isinstance(state, dict):
        raise RuntimeError("broker state missing")
    if int(state.get("schema", -1)) != STATE_SCHEMA:
        raise RuntimeError("broker state schema mismatch")
    basis = state.get("price_basis")
    if basis == PRICE_BASIS:
        state["version"] = VERSION
        state.setdefault("corporate_actions_applied", [])
        return False
    open_positions = [
        f"{market}:{ticker}"
        for market, account in state.get("accounts", {}).items()
        for ticker in account.get("positions", {})
    ]
    if open_positions:
        raise RuntimeError(
            "cannot migrate adjusted-price holdings to raw execution: " + ",".join(open_positions)
        )
    state["version"] = VERSION
    state["price_basis"] = PRICE_BASIS
    state["price_basis_migrated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state.setdefault("corporate_actions_applied", [])
    return True


def _action_key(ticker: str, date: str, kind: str) -> str:
    return f"{ticker}|{date}|{kind}"


def apply_corporate_actions(
    state: dict,
    account: dict,
    ticker: str,
    date: str,
    action_cache: Dict[str, pd.DataFrame],
    now: str,
    market: str,
    cluster: str,
) -> List[dict]:
    """Apply ex-date actions to a position held before that date's open."""
    pos = account.get("positions", {}).get(ticker)
    if not pos:
        return []
    dividend, split = _action_values(action_cache, ticker, date)
    applied = set(state.setdefault("corporate_actions_applied", []))
    rows: List[dict] = []

    if split > 0 and abs(split - 1.0) > 1e-12:
        key = _action_key(ticker, date, "SPLIT")
        if key not in applied:
            old_qty = int(pos.get("qty", 0))
            new_qty_float = old_qty * split
            new_qty = int(round(new_qty_float))
            if old_qty <= 0 or abs(new_qty_float - new_qty) > 1e-8 or new_qty <= 0:
                raise RuntimeError(
                    f"non-integer split requires cash-in-lieu handling: {ticker} {date} ratio={split} qty={old_qty}"
                )
            pos["qty"] = new_qty
            pos["entry_price"] = float(pos["entry_price"]) / split
            if pos.get("last_price"):
                pos["last_price"] = float(pos["last_price"]) / split
            applied.add(key)
            rows.append(pb._order_row(now, date, market, ticker, "SPLIT", "FILLED", "CORPORATE_ACTION", cluster,
                                      qty=new_qty, price=split, fee=0.0, realized_pnl=0.0,
                                      cash_after=float(account.get("cash", 0.0))))

    if dividend > 0:
        key = _action_key(ticker, date, "DIVIDEND")
        if key not in applied:
            qty = int(pos.get("qty", 0))
            credit = qty * dividend
            account["cash"] = float(account.get("cash", 0.0)) + credit
            account["realized_pnl"] = float(account.get("realized_pnl", 0.0)) + credit
            account["dividend_income"] = float(account.get("dividend_income", 0.0)) + credit
            applied.add(key)
            rows.append(pb._order_row(now, date, market, ticker, "DIVIDEND", "FILLED", "CORPORATE_ACTION", cluster,
                                      qty=qty, price=dividend, fee=0.0, realized_pnl=credit,
                                      cash_after=float(account.get("cash", 0.0))))

    state["corporate_actions_applied"] = sorted(applied)
    return rows


def mark_account_raw(
    account: dict,
    price_cache: Dict[str, pd.DataFrame],
    date: str,
    field: str = "Close",
) -> Tuple[float, float]:
    pb._ensure_account_schema(account)
    market_value = 0.0
    for ticker, pos in account.get("positions", {}).items():
        px = raw_price_on(price_cache, ticker, date, field)
        pos["last_price"] = px
        market_value += int(pos.get("qty", 0)) * px
    equity = float(account.get("cash", 0.0)) + market_value
    account["last_equity"] = equity
    account["peak_equity"] = max(float(account.get("peak_equity", equity)), equity)
    pb.update_account_risk(account)
    return equity, market_value


def process_events_raw(
    state: dict,
    events: pd.DataFrame,
    candidate_state: Dict[str, dict],
    cluster_map: Dict[str, str],
):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    price_cache: Dict[str, pd.DataFrame] = {}
    action_cache: Dict[str, pd.DataFrame] = {}
    order_rows: List[dict] = []
    account_rows: List[dict] = []
    marks = state.setdefault("ticker_last_event", {})
    if events.empty:
        return order_rows, account_rows

    unseen = []
    for _, row in events.iterrows():
        ticker, date = str(row["코드"]), str(row["날짜"])
        last = marks.get(ticker)
        if last is None or pd.Timestamp(date) > pd.Timestamp(last):
            unseen.append(row)
    if not unseen:
        return order_rows, account_rows
    work = pd.DataFrame(unseen).sort_values(["날짜", "시장", "코드"])

    for (date, market), group in work.groupby(["날짜", "시장"], sort=True):
        market = str(market)
        if market not in state.get("accounts", {}):
            continue
        account = state["accounts"][market]
        pb._ensure_account_schema(account)
        account.setdefault("dividend_income", 0.0)
        failed_tickers = set()

        # Corporate actions belong to holders from the previous close, before exits/entries.
        for _, row in group.iterrows():
            ticker = str(row["코드"])
            if ticker not in account.get("positions", {}):
                continue
            cluster = str(account["positions"][ticker].get("cluster", cluster_map.get(ticker, ticker)))
            try:
                order_rows.extend(apply_corporate_actions(state, account, ticker, str(date), action_cache, now, market, cluster))
            except Exception as exc:
                failed_tickers.add(ticker)
                order_rows.append(pb._order_row(now, str(date), market, ticker, "ACTION", "ERROR", repr(exc), cluster))

        # Fail closed for a ticker if its corporate action could not be reconciled.
        if account.get("positions"):
            for ticker in list(account["positions"]):
                if ticker in failed_tickers:
                    continue
        try:
            mark_account_raw(account, price_cache, str(date), "Open")
        except Exception as exc:
            # If an existing holding cannot be priced, do not process any account orders for this date.
            for ticker in account.get("positions", {}):
                failed_tickers.add(ticker)
                order_rows.append(pb._order_row(now, str(date), market, ticker, "MARK", "ERROR", repr(exc),
                                                str(account["positions"][ticker].get("cluster", ticker))))
            continue

        # Exits first, including next-session verification revocation.
        for _, row in group.iterrows():
            ticker = str(row["코드"])
            if ticker in failed_tickers:
                continue
            desired_long = str(row["현재포지션"]).upper() == "LONG"
            verified = pb._is_verified_for_date(candidate_state, ticker, str(date))
            must_exit = ticker in account.get("positions", {}) and ((not desired_long) or (not verified))
            if must_exit:
                cluster = str(account["positions"][ticker].get("cluster", cluster_map.get(ticker, ticker)))
                reason = "VERIFICATION_REVOKED" if not verified else "SIGNAL_EXIT"
                try:
                    open_px = raw_price_on(price_cache, ticker, str(date), "Open")
                    fill, err = pb.execute_sell(account, ticker, open_px)
                    if fill:
                        order_rows.append(pb._order_row(now, str(date), market, ticker, "SELL", "FILLED", reason, cluster, **fill))
                    else:
                        order_rows.append(pb._order_row(now, str(date), market, ticker, "SELL", "BLOCKED", err or "SELL_ERROR", cluster))
                except Exception as exc:
                    failed_tickers.add(ticker)
                    order_rows.append(pb._order_row(now, str(date), market, ticker, "SELL", "ERROR", repr(exc), cluster))

        entries = []
        for _, row in group.iterrows():
            ticker = str(row["코드"])
            if ticker in failed_tickers:
                continue
            desired_long = str(row["현재포지션"]).upper() == "LONG"
            if not desired_long or ticker in account.get("positions", {}):
                continue
            cs = candidate_state.get(ticker, {})
            entries.append((str(cs.get("등록시각UTC", "9999")), ticker))
        entries.sort(key=lambda x: (x[0], x[1]))

        for _, ticker in entries:
            cluster = str(cluster_map.get(ticker, ticker))
            if not pb._is_verified_for_date(candidate_state, ticker, str(date)):
                order_rows.append(pb._order_row(now, str(date), market, ticker, "BUY", "BLOCKED", "NOT_FROZEN_VERIFIED", cluster))
                continue
            if bool(account.get("risk_halt")):
                order_rows.append(pb._order_row(now, str(date), market, ticker, "BUY", "BLOCKED", "ACCOUNT_DRAWDOWN_HALT", cluster))
                continue
            if len(account.get("positions", {})) >= pb.MAX_POSITIONS_PER_MARKET:
                order_rows.append(pb._order_row(now, str(date), market, ticker, "BUY", "BLOCKED", "MAX_POSITIONS", cluster))
                continue
            if not pb.cluster_is_free(account, cluster):
                order_rows.append(pb._order_row(now, str(date), market, ticker, "BUY", "BLOCKED", "CLUSTER_OCCUPIED", cluster))
                continue
            try:
                open_px = raw_price_on(price_cache, ticker, str(date), "Open")
                fill, err = pb.execute_buy(account, ticker, market, cluster, open_px, str(date))
                if fill:
                    order_rows.append(pb._order_row(now, str(date), market, ticker, "BUY", "FILLED", "SIGNAL_ENTRY", cluster, **fill))
                else:
                    order_rows.append(pb._order_row(now, str(date), market, ticker, "BUY", "BLOCKED", err or "BUY_ERROR", cluster))
            except Exception as exc:
                failed_tickers.add(ticker)
                order_rows.append(pb._order_row(now, str(date), market, ticker, "BUY", "ERROR", repr(exc), cluster))

        try:
            equity, market_value = mark_account_raw(account, price_cache, str(date), "Close")
        except Exception as exc:
            # Do not advance any ticker watermark if end-of-day account valuation is unreliable.
            for _, row in group.iterrows():
                failed_tickers.add(str(row["코드"]))
            order_rows.append(pb._order_row(now, str(date), market, "ACCOUNT", "MARK", "ERROR", repr(exc), "ACCOUNT"))
            continue

        initial = float(account.get("initial_cash", equity))
        account_rows.append({
            "시각UTC": now, "기준일": str(date), "시장": market, "통화": account["currency"],
            "현금": float(account["cash"]), "보유평가": market_value, "총자산": equity,
            "누적수익률": equity / initial - 1 if initial > 0 else np.nan,
            "최대낙폭": float(account.get("max_drawdown", 0.0)), "현재낙폭": pb.account_drawdown(account),
            "신규매수중지": "⛔" if account.get("risk_halt") else "-",
            "보유종목수": len(account.get("positions", {})), "완료거래": int(account.get("completed_trades", 0)),
            "실현손익": float(account.get("realized_pnl", 0.0)), "배당수익": float(account.get("dividend_income", 0.0)),
            "가격기준": PRICE_BASIS, "브로커": VERSION,
        })
        for _, row in group.iterrows():
            ticker = str(row["코드"])
            if ticker not in failed_tickers:
                marks[ticker] = str(date)

    return order_rows, account_rows


def _snapshot_accounts(state: dict, candidate_state: Dict[str, dict]) -> pd.DataFrame:
    dates = [str(s.get("last_signal_date")) for s in candidate_state.values() if s.get("last_signal_date")]
    date = max(dates) if dates else "-"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    for market, account in state.get("accounts", {}).items():
        pb._ensure_account_schema(account)
        account.setdefault("dividend_income", 0.0)
        initial = float(account["initial_cash"])
        equity = float(account.get("last_equity", initial))
        rows.append({
            "시각UTC": now, "기준일": date, "시장": market, "통화": account["currency"],
            "현금": float(account["cash"]), "보유평가": max(0.0, equity - float(account["cash"])), "총자산": equity,
            "누적수익률": equity / initial - 1 if initial > 0 else np.nan,
            "최대낙폭": float(account.get("max_drawdown", 0.0)), "현재낙폭": pb.account_drawdown(account),
            "신규매수중지": "⛔" if account.get("risk_halt") else "-",
            "보유종목수": len(account.get("positions", {})), "완료거래": int(account.get("completed_trades", 0)),
            "실현손익": float(account.get("realized_pnl", 0.0)), "배당수익": float(account.get("dividend_income", 0.0)),
            "가격기준": PRICE_BASIS, "브로커": VERSION,
        })
    return pd.DataFrame(rows)


def _positions_frame(state: dict) -> pd.DataFrame:
    rows = []
    for market, account in state.get("accounts", {}).items():
        for ticker, pos in account.get("positions", {}).items():
            qty = int(pos.get("qty", 0)); entry = float(pos.get("entry_price", np.nan)); last = float(pos.get("last_price", np.nan))
            rows.append({
                "시장": market, "통화": account.get("currency"), "코드": ticker, "상관군집": pos.get("cluster", ticker),
                "수량": qty, "진입일": pos.get("entry_date", "-"), "평균진입가": entry, "최근가격": last,
                "평가금액": qty * last if np.isfinite(last) else np.nan,
                "미실현손익": qty * (last - entry) - float(pos.get("entry_fee", 0.0)) if np.isfinite(last) else np.nan,
                "가격기준": PRICE_BASIS, "브로커": VERSION,
            })
    cols = ["시장","통화","코드","상관군집","수량","진입일","평균진입가","최근가격","평가금액","미실현손익","가격기준","브로커"]
    return pd.DataFrame(rows, columns=cols)


def write_summary(state: dict, order_rows: List[dict]):
    lines = [
        "# APEX raw-execution shadow paper broker", "",
        f"- broker: {VERSION}", f"- price_basis: {PRICE_BASIS}", "- live orders: NEVER",
        f"- fee/slippage each side: {pb.FEE:.2%} / {pb.SLIPPAGE:.2%}",
        "- dividends: credited as gross virtual cash (taxes ignored)",
        "- stock splits: integer-safe quantity/cost-basis adjustment; ambiguous fractional cases fail closed",
        "- validation/promotion remains independent from broker P/L", "", "## Accounts", "",
    ]
    for market, a in state.get("accounts", {}).items():
        initial = float(a.get("initial_cash", 1.0)); equity = float(a.get("last_equity", initial))
        lines.append(
            f"- {market} {a.get('currency')}: equity={equity:,.2f}, cash={float(a.get('cash',0)):,.2f}, "
            f"return={equity/initial-1:.2%}, max_dd={float(a.get('max_drawdown',0)):.2%}, "
            f"halt={bool(a.get('risk_halt'))}, positions={len(a.get('positions',{}))}, trades={int(a.get('completed_trades',0))}, "
            f"dividends={float(a.get('dividend_income',0)):.2f}"
        )
    lines += ["", "## This run", "", f"- order/action events: {len(order_rows)}"]
    for r in order_rows[-20:]:
        lines.append(f"- {r['체결일']} {r['시장']} {r['코드']} {r['구분']} {r['상태']} {r['사유']}")
    pb.SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    Path("reports").mkdir(exist_ok=True)
    candidate_state = pb._load_candidate_state()
    cluster_map = pb._load_cluster_map()
    events = pb._valid_forward_events()
    state = pb._read_json(pb.BROKER_STATE, None)

    if not isinstance(state, dict):
        state = pb.new_broker_state()
        state["price_basis"] = PRICE_BASIS
        state["version"] = VERSION
        state["corporate_actions_applied"] = []
        pb._initialize_event_watermarks(state, candidate_state)
        migrated = True
    else:
        migrated = migrate_state_to_raw(state)

    for account in state.get("accounts", {}).values():
        pb._ensure_account_schema(account)
        account.setdefault("dividend_income", 0.0)
    state["version"] = VERSION
    state["price_basis"] = PRICE_BASIS

    orders_run, account_rows = process_events_raw(state, events, candidate_state, cluster_map)
    pb.BROKER_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    pb._append_csv(pb.ORDERS, pd.DataFrame(orders_run))
    if account_rows:
        pb._append_csv(pb.ACCOUNT, pd.DataFrame(account_rows))
    elif migrated:
        pb._append_csv(pb.ACCOUNT, _snapshot_accounts(state, candidate_state))
    _positions_frame(state).to_csv(pb.POSITIONS, index=False, encoding="utf-8-sig")
    write_summary(state, orders_run)
    print(pb.SUMMARY.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
