"""Final forward-only paper evidence gate.

This gate never places orders. It prevents a historically attractive strategy
from being labelled forward-validated until it has accumulated enough genuinely
new market observations and completed paper trades.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

STATE = Path("reports/paper_state.json")
LOG = Path("reports/paper_forward.csv")
OUT = Path("reports/promotion_status.csv")
SUMMARY = Path("reports/promotion_status.md")
VERSION = "promotion-gate-1.1-bootstrap"

MIN_OBSERVATIONS = 60
MIN_TRADES = 5
MIN_RETURN = 0.0
MAX_MDD = -0.10
MIN_WINRATE = 0.40
MIN_PF = 1.10
EXTRA_ROUNDTRIP_COST = 0.003
MIN_BOOTSTRAP_POSITIVE_PROB = 0.70

# Fail-fast labels do not delete data or stop tracking. They only prevent promotion.
FAIL_CHECK_OBSERVATIONS = 30
FAIL_RETURN = -0.10
FAIL_MDD = -0.15


def load_state():
    if not STATE.exists():
        return {}
    try:
        obj = json.loads(STATE.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def bootstrap_positive_probability(returns, samples=3000, seed=2026):
    x = np.asarray(returns, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < MIN_TRADES:
        return np.nan
    rng = np.random.default_rng(seed)
    positive = 0
    for _ in range(samples):
        draw = rng.choice(x, size=len(x), replace=True)
        compounded = float(np.prod(1 + draw) - 1)
        positive += compounded > 0
    return float(positive / samples)


def stress_compounded_return(returns):
    x = np.asarray(returns, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan
    stressed = np.maximum(x - EXTRA_ROUNDTRIP_COST, -0.999)
    return float(np.prod(1 + stressed) - 1)


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
        trade_returns = list(s.get("trade_returns", []))
        boot_prob = bootstrap_positive_probability(trade_returns)
        stress_ret = stress_compounded_return(trade_returns)

        reasons = []
        if obs < MIN_OBSERVATIONS:
            reasons.append(f"관측<{MIN_OBSERVATIONS}")
        if trades < MIN_TRADES:
            reasons.append(f"거래<{MIN_TRADES}")
        if fwd <= MIN_RETURN:
            reasons.append("전진수익")
        if mdd < MAX_MDD:
            reasons.append("전진MDD")
        if trades >= MIN_TRADES and (not np.isfinite(wr) or wr < MIN_WINRATE):
            reasons.append("전진승률")
        if trades >= MIN_TRADES and not (np.isinf(pf) or (np.isfinite(pf) and pf >= MIN_PF)):
            reasons.append("전진PF")
        if trades >= MIN_TRADES and (not np.isfinite(stress_ret) or stress_ret <= 0):
            reasons.append("비용스트레스")
        if trades >= MIN_TRADES and (not np.isfinite(boot_prob) or boot_prob < MIN_BOOTSTRAP_POSITIVE_PROB):
            reasons.append("부트스트랩")

        failed = obs >= FAIL_CHECK_OBSERVATIONS and (fwd <= FAIL_RETURN or mdd <= FAIL_MDD)
        passed = (not failed) and len(reasons) == 0
        if failed:
            final_status = "전진실패"
        elif passed:
            final_status = "전진검증완료"
        else:
            final_status = "관찰중"

        rows.append({
            "승격가능": "✅" if passed else "❌",
            "최종상태": final_status,
            "종목": s.get("종목", ticker),
            "코드": ticker,
            "전략": s.get("전략", "?"),
            "관측거래일": obs,
            "완료거래": trades,
            "전진누적수익": fwd,
            "전진MDD": mdd,
            "승률": wr,
            "PF": pf,
            "비용스트레스수익": stress_ret,
            "부트스트랩양수확률": boot_prob,
            "현재포지션": latest.get("현재포지션", "-") if len(latest) else "-",
            "대기조건": "-" if passed else ("손실/MDD 중단기준" if failed else ", ".join(reasons)),
            "게이트": VERSION,
        })

    result = pd.DataFrame(rows)
    result.to_csv(OUT, index=False, encoding="utf-8-sig")
    passed = result[result["승격가능"] == "✅"] if not result.empty else result
    failed = result[result["최종상태"] == "전진실패"] if not result.empty else result
    lines = [
        "# APEX final promotion gate", "",
        f"- gate: {VERSION}",
        f"- tracked candidates: {len(result)}",
        f"- forward-validated: {len(passed)}",
        f"- forward-failed: {len(failed)}", "",
        "Promotion requires 60 new market observations, 5 completed paper trades, positive forward return,",
        "controlled drawdown, minimum win/PF quality, doubled-cost stress resilience, and bootstrap support.",
        "No status places orders or guarantees future returns.", "",
    ]
    if not result.empty:
        lines += ["## Status", ""]
        for _, r in result.iterrows():
            bp = r["부트스트랩양수확률"]
            bp_txt = "-" if not np.isfinite(bp) else f"{bp:.1%}"
            lines.append(
                f"- {r['최종상태']} {r['종목']} ({r['코드']}): obs={r['관측거래일']}, "
                f"trades={r['완료거래']}, forward={r['전진누적수익']:.2%}, "
                f"bootstrap={bp_txt}, waiting={r['대기조건']}"
            )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
