"""Offline accounting/risk invariant check for the APEX shadow paper broker."""
from __future__ import annotations

from pathlib import Path
import json
import math
import pandas as pd

from tools.paper_broker import (
    BROKER_STATE,
    HARD_DRAWDOWN_HALT,
    MAX_POSITIONS_PER_MARKET,
    ORDERS,
    STATE_SCHEMA,
)

OUT = Path("reports/paper_broker_health.json")
SUMMARY = Path("reports/paper_broker_health.md")
VERSION = "broker-health-1.1-raw-execution"
EXPECTED_PRICE_BASIS = "RAW_EXECUTION"
EXPECTED_BROKER_PREFIX = "paper-broker-1.4"


def validate_state(state: dict, orders: pd.DataFrame | None = None):
    errors = []
    if not isinstance(state, dict):
        return ["state-not-dict"]
    if int(state.get("schema", -1)) != STATE_SCHEMA:
        errors.append("schema-mismatch")
    if str(state.get("price_basis", "")) != EXPECTED_PRICE_BASIS:
        errors.append("price-basis-not-raw-execution")
    if not str(state.get("version", "")).startswith(EXPECTED_BROKER_PREFIX):
        errors.append("broker-version-not-raw-execution")
    actions = state.get("corporate_actions_applied", [])
    if not isinstance(actions, list) or len(actions) != len(set(map(str, actions))):
        errors.append("corporate-action-ledger-invalid")

    accounts = state.get("accounts", {})
    if not isinstance(accounts, dict) or not accounts:
        errors.append("accounts-missing")
        return errors

    for market, account in accounts.items():
        try:
            cash = float(account.get("cash", float("nan")))
            equity = float(account.get("last_equity", float("nan")))
            peak = float(account.get("peak_equity", float("nan")))
            max_dd = float(account.get("max_drawdown", 0.0))
            dividends = float(account.get("dividend_income", 0.0))
        except Exception:
            errors.append(f"{market}:numeric-state")
            continue
        if not all(math.isfinite(x) for x in [cash, equity, peak, max_dd, dividends]):
            errors.append(f"{market}:nonfinite-state")
        if cash < -1e-6:
            errors.append(f"{market}:negative-cash")
        if equity <= 0 or peak <= 0:
            errors.append(f"{market}:nonpositive-equity")
        if dividends < -1e-9:
            errors.append(f"{market}:negative-dividend-income")
        positions = account.get("positions", {})
        if len(positions) > MAX_POSITIONS_PER_MARKET:
            errors.append(f"{market}:too-many-positions")
        clusters = []
        for ticker, pos in positions.items():
            qty = int(pos.get("qty", 0))
            entry = float(pos.get("entry_price", 0.0))
            cost = float(pos.get("cost_total", 0.0))
            cluster = str(pos.get("cluster", ticker))
            clusters.append(cluster)
            if qty <= 0:
                errors.append(f"{market}:{ticker}:bad-qty")
            if not math.isfinite(entry) or entry <= 0:
                errors.append(f"{market}:{ticker}:bad-entry")
            if not math.isfinite(cost) or cost <= 0:
                errors.append(f"{market}:{ticker}:bad-cost")
        if len(clusters) != len(set(clusters)):
            errors.append(f"{market}:duplicate-correlation-cluster")
        if max_dd <= HARD_DRAWDOWN_HALT and not bool(account.get("risk_halt")):
            errors.append(f"{market}:drawdown-halt-missing")

    for ticker, date in state.get("ticker_last_event", {}).items():
        try:
            pd.Timestamp(date)
        except Exception:
            errors.append(f"watermark:{ticker}:bad-date")

    if orders is not None and not orders.empty:
        needed = {"체결일", "시장", "코드", "구분", "상태"}
        if needed.issubset(orders.columns):
            filled = orders[orders["상태"].astype(str) == "FILLED"].copy()
            if not filled.empty:
                dup = filled.duplicated(["체결일", "시장", "코드", "구분"], keep=False)
                if dup.any():
                    errors.append("duplicate-filled-order-key")
    return errors


def main():
    if not BROKER_STATE.exists():
        raise SystemExit("paper broker state missing")
    state = json.loads(BROKER_STATE.read_text(encoding="utf-8"))
    try:
        orders = pd.read_csv(ORDERS) if ORDERS.exists() and ORDERS.stat().st_size else pd.DataFrame()
    except Exception:
        orders = pd.DataFrame()
    errors = validate_state(state, orders)
    result = {
        "version": VERSION,
        "ok": len(errors) == 0,
        "errors": errors,
        "broker_version": state.get("version"),
        "price_basis": state.get("price_basis"),
        "accounts": len(state.get("accounts", {})),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# APEX shadow broker health", "",
        f"- health: {VERSION}",
        f"- broker: {state.get('version')}",
        f"- price_basis: {state.get('price_basis')}",
        f"- ok: {result['ok']}",
        f"- errors: {len(errors)}",
    ]
    if errors:
        lines += ["", "## Errors", ""] + [f"- {x}" for x in errors]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if errors:
        raise SystemExit("broker health check failed: " + ", ".join(errors))


if __name__ == "__main__":
    main()
