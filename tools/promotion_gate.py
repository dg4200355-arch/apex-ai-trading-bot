"""Final paper-evidence gate.

This gate cannot place orders. It only prevents a backtest/confirmation candidate
from being labelled ready until enough forward-only observations exist.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

STATE = Path("reports/paper_state.json")
LOG = Path("reports/paper_forward.csv")
OUT = Path("reports/promotion_status.csv")
SUMMARY = Path("reports/promotion_status.md")
VERSION = "promotion-gate-1.0"

MIN_OBSERVATIONS = 30
MIN_TRADES = 3
MIN_RETURN = 0.0
MAX_MDD = -0.10
MIN_WINRATE = 0.40
MIN_PF = 1.10


def load_state():
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main():
    Path("reports").mkdir(exist_ok=True)
    state = load_state()
    if LOG.exists() and LOG.stat().st_size:
        try:
            log = pd.read_csv(LOG)
        except Exception:
            log = pd.DataFrame()
    else:
        log = pd.DataFrame()

    rows = []
    for ticker, s in state.items():
        latest = pd.Series(dtype=object)
        if not log.empty and "코드" in log.columns:
            hit = log[log["코드"].astype(str) == str(ticker)]
            if not hit.empty:
                latest = hit.iloc[-1]

        obs = int(s.get("observations", 0))
        trades = int(s.get("completed_trades", 0))
        wins = int(s.get("wins", 0))
        gp = float(s.get("gross_profit", 0.0))
        gl = float(s.get("gross_loss", 0.0))
        pf = gp / gl if gl > 0 else (np.inf if trades > 0 and gp > 0 else np.nan)
        wr = wins / trades if trades else np.nan
        fwd = float(latest.get("전진누적수익", 0.0)) if len(latest) else 0.0
        mdd = float(s.get("forward_mdd", 0.0))

        reasons = []
        if obs < MIN_OBSERVATIONS: reasons.append(f"관측<{MIN_OBSERVATIONS}")
        if trades < MIN_TRADES: reasons.append(f"거래<{MIN_TRADES}")
        if fwd <= MIN_RETURN: reasons.append("전진수익")
        if mdd < MAX_MDD: reasons.append("전진MDD")
        if trades >= MIN_TRADES and (not np.isfinite(wr) or wr < MIN_WINRATE): reasons.append("전진승률")
        if trades >= MIN_TRADES and not (np.isinf(pf) or (np.isfinite(pf) and pf >= MIN_PF)): reasons.append("전진PF")

        passed = len(reasons) == 0
        rows.append({
            "승격가능": "✅" if passed else "❌",
            "최종상태": "전진검증완료" if passed else "관찰중",
            "종목": s.get("종목", ticker),
            "코드": ticker,
            "전략": s.get("전략", "?"),
            "관측거래일": obs,
            "완료거래": trades,
            "전진누적수익": fwd,
            "전진MDD": mdd,
            "승률": wr,
            "PF": pf,
            "현재포지션": latest.get("현재포지션", "-") if len(latest) else "-",
            "대기조건": "-" if passed else ", ".join(reasons),
            "게이트": VERSION,
        })

    result = pd.DataFrame(rows)
    result.to_csv(OUT, index=False, encoding="utf-8-sig")
    passed = result[result["승격가능"] == "✅"] if not result.empty else result
    lines = [
        "# APEX final promotion gate", "",
        f"- gate: {VERSION}",
        f"- tracked candidates: {len(result)}",
        f"- forward-validated: {len(passed)}", "",
        "This status does not place orders or guarantee future returns.", "",
    ]
    if not result.empty:
        lines += ["## Status", ""]
        for _, r in result.iterrows():
            lines.append(
                f"- {r['최종상태']} {r['종목']} ({r['코드']}): obs={r['관측거래일']}, "
                f"trades={r['완료거래']}, forward={r['전진누적수익']:.2%}, waiting={r['대기조건']}"
            )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
