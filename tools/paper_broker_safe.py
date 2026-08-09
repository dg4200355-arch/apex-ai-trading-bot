"""Transactional entrypoint for the RAW_EXECUTION APEX shadow broker.

The broker computes an entire forward cycle in memory and persists nothing unless
all pricing, corporate-action, order and account-mark operations succeed.

Corporate-action timing policy
------------------------------
- Stock splits are applied before the ex-date open because raw prices reflect them.
- Dividend entitlement is captured from the position held before the ex-date open.
- Dividend cash is credited only after that day's entry/exit decisions, so it cannot
  finance a same-day new paper purchase. This is intentionally conservative because
  Yahoo exposes ex-date actions, not the later cash payment date.

No live orders are ever sent.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from tools import paper_broker_raw as raw

FAILURE_REPORT = Path("reports/failed_paper_broker.json")
LEGACY_CORE_VERSION = "paper-broker-1.3-verification-timing"
pb = raw.pb

# paper_broker_raw historically changed the helper module's VERSION during import.
# The persistent RAW broker version belongs to raw.VERSION/state, not to the shared
# accounting helper. Restore the helper value and stamp every emitted row locally.
pb.VERSION = LEGACY_CORE_VERSION


def order_row(now: str, date: str, market: str, ticker: str, side: str, status: str,
              reason: str, cluster: str, qty=0, price=np.nan, fee=0.0,
              realized_pnl=0.0, cash_after=np.nan):
    row = pb._order_row(
        now, date, market, ticker, side, status, reason, cluster,
        qty=qty, price=price, fee=fee, realized_pnl=realized_pnl, cash_after=cash_after,
    )
    row["브로커"] = raw.VERSION
    return row


def execution_errors(order_rows):
    return [r for r in order_rows if str(r.get("상태")) == "ERROR"]


def _action_key(ticker: str, date: str, kind: str) -> str:
    return f"{ticker}|{date}|{kind}"


def prepare_preopen_actions(
    state: dict,
    account: dict,
    ticker: str,
    date: str,
    action_cache: Dict[str, pd.DataFrame],
    now: str,
    market: str,
    cluster: str,
) -> Tuple[List[dict], List[dict]]:
    """Apply splits now and capture dividend entitlement without crediting cash."""
    pos = account.get("positions", {}).get(ticker)
    if not pos:
        return [], []
    dividend, split = raw._action_values(action_cache, ticker, date)
    applied = set(state.setdefault("corporate_actions_applied", []))
    rows: List[dict] = []
    entitlements: List[dict] = []

    # Simultaneous split+dividend semantics can be vendor-specific. Do not guess.
    if dividend > 0 and split > 0 and abs(split - 1.0) > 1e-12:
        raise RuntimeError(f"simultaneous dividend/split requires manual reconciliation: {ticker} {date}")

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
            rows.append(order_row(
                now, date, market, ticker, "SPLIT", "FILLED", "CORPORATE_ACTION", cluster,
                qty=new_qty, price=split, fee=0.0, realized_pnl=0.0,
                cash_after=float(account.get("cash", 0.0)),
            ))

    if dividend > 0:
        key = _action_key(ticker, date, "DIVIDEND")
        if key not in applied:
            qty = int(pos.get("qty", 0))
            if qty <= 0:
                raise RuntimeError(f"invalid dividend entitlement quantity: {ticker} {date} qty={qty}")
            entitlements.append({
                "key": key,
                "ticker": ticker,
                "date": date,
                "market": market,
                "cluster": cluster,
                "qty": qty,
                "per_share": float(dividend),
            })

    state["corporate_actions_applied"] = sorted(applied)
    return rows, entitlements


def settle_dividend_entitlements(
    state: dict,
    account: dict,
    entitlements: List[dict],
    now: str,
) -> List[dict]:
    """Credit captured ex-date entitlements after same-day order sizing is finished."""
    applied = set(state.setdefault("corporate_actions_applied", []))
    rows: List[dict] = []
    for ent in entitlements:
        key = str(ent["key"])
        if key in applied:
            continue
        qty = int(ent["qty"])
        per_share = float(ent["per_share"])
        credit = qty * per_share
        if qty <= 0 or not np.isfinite(credit) or credit <= 0:
            raise RuntimeError(f"invalid dividend credit: {ent}")
        account["cash"] = float(account.get("cash", 0.0)) + credit
        account["realized_pnl"] = float(account.get("realized_pnl", 0.0)) + credit
        account["dividend_income"] = float(account.get("dividend_income", 0.0)) + credit
        applied.add(key)
        rows.append(order_row(
            now, str(ent["date"]), str(ent["market"]), str(ent["ticker"]),
            "DIVIDEND", "FILLED", "EX_DATE_ENTITLEMENT_POST_ORDER_CREDIT", str(ent["cluster"]),
            qty=qty, price=per_share, fee=0.0, realized_pnl=credit,
            cash_after=float(account.get("cash", 0.0)),
        ))
    state["corporate_actions_applied"] = sorted(applied)
    return rows


def process_events_transactional(
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
        date, market = str(date), str(market)
        if market not in state.get("accounts", {}):
            continue
        account = state["accounts"][market]
        pb._ensure_account_schema(account)
        account.setdefault("dividend_income", 0.0)
        failed_tickers = set()
        dividend_entitlements: List[dict] = []

        # Apply/capture actions for every existing holding, even if one ticker's
        # forward row is temporarily absent while another market row exists.
        for ticker in list(account.get("positions", {})):
            cluster = str(account["positions"][ticker].get("cluster", cluster_map.get(ticker, ticker)))
            try:
                rows, ents = prepare_preopen_actions(
                    state, account, ticker, date, action_cache, now, market, cluster
                )
                order_rows.extend(rows)
                dividend_entitlements.extend(ents)
            except Exception as exc:
                failed_tickers.add(ticker)
                order_rows.append(order_row(now, date, market, ticker, "ACTION", "ERROR", repr(exc), cluster))

        try:
            raw.mark_account_raw(account, price_cache, date, "Open")
        except Exception as exc:
            for ticker in account.get("positions", {}):
                failed_tickers.add(ticker)
                order_rows.append(order_row(
                    now, date, market, ticker, "MARK", "ERROR", repr(exc),
                    str(account["positions"][ticker].get("cluster", ticker)),
                ))
            continue

        # Exits first so released cash/cluster capacity is available for new entries.
        for _, row in group.iterrows():
            ticker = str(row["코드"])
            if ticker in failed_tickers:
                continue
            desired_long = str(row["현재포지션"]).upper() == "LONG"
            verified = pb._is_verified_for_date(candidate_state, ticker, date)
            must_exit = ticker in account.get("positions", {}) and ((not desired_long) or (not verified))
            if not must_exit:
                continue
            cluster = str(account["positions"][ticker].get("cluster", cluster_map.get(ticker, ticker)))
            reason = "VERIFICATION_REVOKED" if not verified else "SIGNAL_EXIT"
            try:
                open_px = raw.raw_price_on(price_cache, ticker, date, "Open")
                fill, err = pb.execute_sell(account, ticker, open_px)
                if fill:
                    order_rows.append(order_row(now, date, market, ticker, "SELL", "FILLED", reason, cluster, **fill))
                else:
                    order_rows.append(order_row(now, date, market, ticker, "SELL", "BLOCKED", err or "SELL_ERROR", cluster))
            except Exception as exc:
                failed_tickers.add(ticker)
                order_rows.append(order_row(now, date, market, ticker, "SELL", "ERROR", repr(exc), cluster))

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
            if not pb._is_verified_for_date(candidate_state, ticker, date):
                order_rows.append(order_row(now, date, market, ticker, "BUY", "BLOCKED", "NOT_FROZEN_VERIFIED", cluster))
                continue
            if bool(account.get("risk_halt")):
                order_rows.append(order_row(now, date, market, ticker, "BUY", "BLOCKED", "ACCOUNT_DRAWDOWN_HALT", cluster))
                continue
            if len(account.get("positions", {})) >= pb.MAX_POSITIONS_PER_MARKET:
                order_rows.append(order_row(now, date, market, ticker, "BUY", "BLOCKED", "MAX_POSITIONS", cluster))
                continue
            if not pb.cluster_is_free(account, cluster):
                order_rows.append(order_row(now, date, market, ticker, "BUY", "BLOCKED", "CLUSTER_OCCUPIED", cluster))
                continue
            try:
                open_px = raw.raw_price_on(price_cache, ticker, date, "Open")
                fill, err = pb.execute_buy(account, ticker, market, cluster, open_px, date)
                if fill:
                    order_rows.append(order_row(now, date, market, ticker, "BUY", "FILLED", "SIGNAL_ENTRY", cluster, **fill))
                else:
                    order_rows.append(order_row(now, date, market, ticker, "BUY", "BLOCKED", err or "BUY_ERROR", cluster))
            except Exception as exc:
                failed_tickers.add(ticker)
                order_rows.append(order_row(now, date, market, ticker, "BUY", "ERROR", repr(exc), cluster))

        # Dividend cash is recognized only after all same-day order sizing.
        try:
            order_rows.extend(settle_dividend_entitlements(state, account, dividend_entitlements, now))
        except Exception as exc:
            order_rows.append(order_row(now, date, market, "ACCOUNT", "DIVIDEND", "ERROR", repr(exc), "ACCOUNT"))
            continue

        try:
            equity, market_value = raw.mark_account_raw(account, price_cache, date, "Close")
        except Exception as exc:
            for _, row in group.iterrows():
                failed_tickers.add(str(row["코드"]))
            order_rows.append(order_row(now, date, market, "ACCOUNT", "MARK", "ERROR", repr(exc), "ACCOUNT"))
            continue

        initial = float(account.get("initial_cash", equity))
        account_rows.append({
            "시각UTC": now, "기준일": date, "시장": market, "통화": account["currency"],
            "현금": float(account["cash"]), "보유평가": market_value, "총자산": equity,
            "누적수익률": equity / initial - 1 if initial > 0 else np.nan,
            "최대낙폭": float(account.get("max_drawdown", 0.0)), "현재낙폭": pb.account_drawdown(account),
            "신규매수중지": "⛔" if account.get("risk_halt") else "-",
            "보유종목수": len(account.get("positions", {})), "완료거래": int(account.get("completed_trades", 0)),
            "실현손익": float(account.get("realized_pnl", 0.0)), "배당수익": float(account.get("dividend_income", 0.0)),
            "가격기준": raw.PRICE_BASIS, "브로커": raw.VERSION,
        })
        for _, row in group.iterrows():
            ticker = str(row["코드"])
            if ticker not in failed_tickers:
                marks[ticker] = date

    return order_rows, account_rows


def main():
    Path("reports").mkdir(exist_ok=True)
    candidate_state = pb._load_candidate_state()
    cluster_map = pb._load_cluster_map()
    events = pb._valid_forward_events()
    state = pb._read_json(pb.BROKER_STATE, None)

    if not isinstance(state, dict):
        state = pb.new_broker_state()
        state["price_basis"] = raw.PRICE_BASIS
        state["version"] = raw.VERSION
        state["corporate_actions_applied"] = []
        pb._initialize_event_watermarks(state, candidate_state)
        migrated = True
    else:
        migrated = raw.migrate_state_to_raw(state)

    for account in state.get("accounts", {}).values():
        pb._ensure_account_schema(account)
        account.setdefault("dividend_income", 0.0)
    state["version"] = raw.VERSION
    state["price_basis"] = raw.PRICE_BASIS

    orders_run, account_rows = process_events_transactional(state, events, candidate_state, cluster_map)
    errors = execution_errors(orders_run)
    if errors:
        FAILURE_REPORT.write_text(json.dumps({
            "at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "broker": raw.VERSION,
            "errors": errors,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit(f"raw paper broker failed closed: {len(errors)} execution/accounting errors")
    if FAILURE_REPORT.exists():
        FAILURE_REPORT.unlink()

    # Commit the in-memory transaction only after every event is valid.
    pb.BROKER_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    pb._append_csv(pb.ORDERS, pd.DataFrame(orders_run))
    if account_rows:
        pb._append_csv(pb.ACCOUNT, pd.DataFrame(account_rows))
    elif migrated:
        pb._append_csv(pb.ACCOUNT, raw._snapshot_accounts(state, candidate_state))
    raw._positions_frame(state).to_csv(pb.POSITIONS, index=False, encoding="utf-8-sig")
    raw.write_summary(state, orders_run)
    print(pb.SUMMARY.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
