"""Final forward-only paper evidence gate.

This gate never places orders. A candidate must first be re-verified by the current
immutable stage-2 confirmation engine with the exact same admitted strategy and
parameters. Only then can forward evidence be considered for promotion.
"""
from pathlib import Path
import json
from math import comb
import numpy as np
import pandas as pd

STATE = Path("reports/paper_state.json")
LOG = Path("reports/paper_forward.csv")
OUT = Path("reports/promotion_status.csv")
SUMMARY = Path("reports/promotion_status.md")
VERSION = "promotion-gate-1.3-frozen-admission"

MIN_OBSERVATIONS = 60
MIN_TRADES = 5
MIN_RETURN = 0.0
MAX_MDD = -0.10
MIN_WINRATE = 0.40
MIN_PF = 1.10
EXTRA_ROUNDTRIP_COST = 0.003
MIN_BOOTSTRAP_POSITIVE_PROB = 0.70
MAX_FORWARD_SIGN_Q = 0.20

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


def sign_test_pvalue(returns):
    x = np.asarray(returns, dtype=float)
    x = x[np.isfinite(x)]
    x = x[x != 0]
    n = int(len(x))
    if n < MIN_TRADES:
        return np.nan
    wins = int(np.sum(x > 0))
    tail = sum(comb(n, k) for k in range(wins, n + 1))
    return float(tail / (2 ** n))


def bh_qvalues(values, family_size=None):
    p = np.asarray(values, dtype=float)
    q = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    if not valid.any():
        return q
    pv = p[valid]
    order = np.argsort(pv)
    ranked = pv[order]
    m = max(int(family_size or len(ranked)), len(ranked))
    raw = ranked * m / np.arange(1, len(ranked) + 1)
    adj = np.minimum.accumulate(raw[::-1])[::-1]
    out = np.empty(len(ranked))
    out[order] = np.clip(adj, 0, 1)
    q[np.where(valid)[0]] = out
    return q


def latest_log_row(log: pd.DataFrame, ticker: str):
    if log.empty or "코드" not in log.columns:
        return pd.Series(dtype=object)
    hit = log[log["코드"].astype(str) == str(ticker)]
    return hit.iloc[-1] if not hit.empty else pd.Series(dtype=object)


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

    metrics = []
    for ticker, s in state.items():
        latest = latest_log_row(log, ticker)
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
        metrics.append({
            "ticker": ticker,
            "state": s,
            "latest": latest,
            "obs": obs,
            "trades": trades,
            "wr": wr,
            "pf": pf,
            "fwd": fwd,
            "mdd": mdd,
            "stress_ret": stress_compounded_return(trade_returns),
            "boot_prob": bootstrap_positive_probability(trade_returns),
            "sign_p": sign_test_pvalue(trade_returns),
            "frozen_verified": bool(s.get("frozen_verified", False)),
        })

    sign_q = bh_qvalues([m["sign_p"] for m in metrics], family_size=max(1, len(metrics)))
    rows = []
    for i, m in enumerate(metrics):
        ticker, s, latest = m["ticker"], m["state"], m["latest"]
        obs, trades, wr, pf = m["obs"], m["trades"], m["wr"], m["pf"]
        fwd, mdd = m["fwd"], m["mdd"]
        stress_ret, boot_prob, sign_p = m["stress_ret"], m["boot_prob"], m["sign_p"]
        frozen_verified = m["frozen_verified"]
        fq = float(sign_q[i]) if np.isfinite(sign_q[i]) else np.nan

        reasons = []
        if not frozen_verified:
            reasons.append("동결재검증")
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
        if trades >= MIN_TRADES and (not np.isfinite(fq) or fq > MAX_FORWARD_SIGN_Q):
            reasons.append("전진다중검정")

        failed = obs >= FAIL_CHECK_OBSERVATIONS and (fwd <= FAIL_RETURN or mdd <= FAIL_MDD)
        passed = frozen_verified and (not failed) and len(reasons) == 0
        final_status = "전진실패" if failed else ("전진검증완료" if passed else "관찰중")

        rows.append({
            "승격가능": "✅" if passed else "❌",
            "최종상태": final_status,
            "동결검증": "FROZEN_VERIFIED" if frozen_verified else "LEGACY_LOCKED",
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
            "방향성p": sign_p,
            "전진다중검정q": fq,
            "현재포지션": latest.get("현재포지션", "-") if len(latest) else "-",
            "대기조건": "-" if passed else ("손실/MDD 중단기준" if failed else ", ".join(reasons)),
            "게이트": VERSION,
        })

    result = pd.DataFrame(rows)
    result.to_csv(OUT, index=False, encoding="utf-8-sig")
    passed = result[result["승격가능"] == "✅"] if not result.empty else result
    failed = result[result["최종상태"] == "전진실패"] if not result.empty else result
    verified = result[result["동결검증"] == "FROZEN_VERIFIED"] if not result.empty else result
    lines = [
        "# APEX final promotion gate", "",
        f"- gate: {VERSION}",
        f"- tracked candidates: {len(result)}",
        f"- frozen-confirm verified: {len(verified)}",
        f"- forward-validated: {len(passed)}",
        f"- forward-failed: {len(failed)}", "",
        "Promotion first requires immutable stage-2 re-verification of the exact admitted strategy and parameters.",
        "It then requires 60 new observations, 5 completed paper trades, positive return, controlled drawdown,",
        "win/PF quality, doubled-cost stress resilience, bootstrap support, and a candidate-family adjusted sign test.",
        "No status places orders or guarantees future returns.", "",
    ]
    if not result.empty:
        lines += ["## Status", ""]
        for _, r in result.iterrows():
            bp = r["부트스트랩양수확률"]
            bp_txt = "-" if not np.isfinite(bp) else f"{bp:.1%}"
            fq = r["전진다중검정q"]
            fq_txt = "-" if not np.isfinite(fq) else f"{fq:.3f}"
            lines.append(
                f"- {r['최종상태']} {r['종목']} ({r['코드']}): frozen={r['동결검증']}, obs={r['관측거래일']}, "
                f"trades={r['완료거래']}, forward={r['전진누적수익']:.2%}, bootstrap={bp_txt}, "
                f"forward_q={fq_txt}, waiting={r['대기조건']}"
            )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
