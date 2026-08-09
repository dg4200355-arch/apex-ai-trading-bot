"""Transactional entrypoint for the raw-execution APEX shadow broker.

All state mutations happen in memory first. If any execution/corporate-action/mark
ERROR is produced, nothing is persisted and the previous known-good account remains
unchanged. No live orders are placed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

import pandas as pd

from tools import paper_broker_raw as raw

FAILURE_REPORT = Path("reports/failed_paper_broker.json")


def execution_errors(order_rows):
    return [r for r in order_rows if str(r.get("상태")) == "ERROR"]


def main():
    Path("reports").mkdir(exist_ok=True)
    pb = raw.pb
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

    orders_run, account_rows = raw.process_events_raw(state, events, candidate_state, cluster_map)
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
