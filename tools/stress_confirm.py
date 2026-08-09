"""Second-stage robustness confirmation for APEX v8.x candidates.

This script does NOT search for a better strategy on the hidden TEST period.
It reconstructs the strategy chosen by the primary scan, freezes that choice,
and then tries to break it with:
  1) higher transaction costs,
  2) nearby parameter perturbations,
  3) a longer 10-year regime-history stress test.

The purpose is rejection, not optimization. No live orders are placed.
"""
from __future__ import annotations

from pathlib import Path
import json
import math
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from engine import (
    build_rule_signal,
    fit_ai_predict,
    make_features,
    perf_from_signal,
    select_ai,
    select_rule,
)

REPORT = Path("reports/latest_validation.csv")
OUT = Path("reports/latest_confirmation.csv")
SUMMARY = Path("reports/latest_confirmation.md")
BASE_FEE = 0.0015
STRESS_FEE = 0.0025
FEES = [0.0015, 0.0025, 0.0035]
ENGINE_VERSION = "8.3-stress-confirm"


def dl(ticker: str, period: str) -> pd.DataFrame:
    d = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
    if d is None or d.empty:
        raise RuntimeError(f"no data: {ticker}")
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    need = ["Open", "High", "Low", "Close", "Volume"]
    if any(c not in d.columns for c in need):
        raise RuntimeError(f"bad OHLCV: {ticker}")
    return d[need].dropna()


def reconstruct_choice(data: pd.DataFrame, future: int = 5):
    split = int(len(data) * 0.75)
    pretest = data.iloc[:split].copy()
    rule = select_rule(pretest, data, BASE_FEE)
    ai = select_ai(pretest, future, BASE_FEE, True) if pretest["target"].nunique() > 1 else None
    choices = [c for c in [rule, ai] if c is not None]
    if not choices:
        raise ValueError("no reconstructable strategy")
    return max(choices, key=lambda c: c.validation_score), pretest, data.iloc[split:].copy()


def signal_for_choice(data: pd.DataFrame, pretest: pd.DataFrame, target: pd.DataFrame, choice, future: int = 5) -> pd.Series:
    if choice.kind == "AI":
        p = fit_ai_predict(pretest, target, True)
        return (
            (pd.Series(p, index=target.index) >= float(choice.params["threshold"]))
            & (target["Close"] > target["ema55"])
            & target["rsi"].between(45, 78)
        )
    full = build_rule_signal(data, choice.kind, choice.params)
    return full.reindex(target.index).fillna(False)


def nearby_params(kind: str, params: Dict[str, float]) -> List[Dict[str, float]]:
    base = dict(params)
    out = [base]
    if kind == "추세":
        for delta in (-4, 4):
            p = dict(base); p["rsi_max"] = float(np.clip(base["rsi_max"] + delta, 60, 90)); out.append(p)
        for delta in (-0.10, 0.10):
            p = dict(base); p["vol_min"] = float(np.clip(base.get("vol_min", 0.65) + delta, 0.35, 1.50)); out.append(p)
    elif kind == "반전":
        for delta in (-0.05, 0.05):
            p = dict(base); p["bb"] = float(np.clip(base["bb"] + delta, 0.03, 0.40)); out.append(p)
        for delta in (-3, 3):
            p = dict(base); p["rsi"] = float(np.clip(base["rsi"] + delta, 25, 50)); out.append(p)
    elif kind == "돌파":
        for delta in (-0.15, 0.15):
            p = dict(base); p["vol"] = float(np.clip(base["vol"] + delta, 0.50, 1.80)); out.append(p)
        p = dict(base); p["lookback"] = 55 if int(base["lookback"]) == 20 else 20; out.append(p)
    elif kind == "AI":
        for delta in (-0.04, 0.04):
            p = dict(base); p["threshold"] = float(np.clip(base["threshold"] + delta, 0.48, 0.75)); out.append(p)
    # de-duplicate while preserving order
    unique = []
    seen = set()
    for p in out:
        key = json.dumps(p, sort_keys=True)
        if key not in seen:
            unique.append(p); seen.add(key)
    return unique


def fixed_signal(data: pd.DataFrame, pretest: pd.DataFrame, target: pd.DataFrame, kind: str, params: Dict[str, float]) -> pd.Series:
    if kind == "AI":
        p = fit_ai_predict(pretest, target, True)
        return (
            (pd.Series(p, index=target.index) >= float(params["threshold"]))
            & (target["Close"] > target["ema55"])
            & target["rsi"].between(45, 78)
        )
    return build_rule_signal(data, kind, params).reindex(target.index).fillna(False)


def history_stress(data10: pd.DataFrame, kind: str, params: Dict[str, float], future: int = 5) -> Tuple[float, float, float, int]:
    """Walk through four later-history windows with the strategy parameters frozen.

    Rule strategies use exactly the same fixed parameters. AI uses expanding-window
    refits but keeps the threshold and filters fixed; the model is never fit on the
    window it is evaluated on.
    """
    n = len(data10)
    start = max(500, int(n * 0.35))
    edges = np.linspace(start, n, 5, dtype=int)
    rets: List[float] = []
    mdds: List[float] = []
    trades = 0
    for i in range(4):
        a, b = int(edges[i]), int(edges[i + 1])
        target = data10.iloc[a:b].copy()
        if len(target) < 100:
            continue
        if kind == "AI":
            train_end = max(0, a - future)
            train = data10.iloc[:train_end].copy()
            if len(train) < 450 or train["target"].nunique() < 2:
                continue
            sig = fixed_signal(data10, train, target, kind, params)
        else:
            sig = fixed_signal(data10, data10.iloc[:a], target, kind, params)
        perf = perf_from_signal(target, sig, STRESS_FEE)
        rets.append(perf.ret); mdds.append(perf.mdd); trades += perf.trades
    if not rets:
        return 0.0, -1.0, -1.0, 0
    return float(np.mean(np.array(rets) > 0)), float(np.median(rets)), float(np.min(mdds)), int(trades)


def finite_pf(x: float) -> float:
    return float(x) if np.isfinite(x) else 99.0


def confirm_one(row: pd.Series) -> Dict[str, object]:
    ticker = str(row["코드"])
    market = str(row["시장"])
    benchmark = "^KS11" if market == "KR" else "SPY"

    raw5, bench5 = dl(ticker, "5y"), dl(benchmark, "5y")
    data5 = make_features(raw5, bench5, future=5, target_pct=.01)
    choice, pretest5, test5 = reconstruct_choice(data5, future=5)

    # Verify we are confirming the same strategy family emitted by the scan.
    scan_kind = str(row["선택전략"])
    if choice.kind != scan_kind:
        raise ValueError(f"strategy drift: scan={scan_kind}, reconstructed={choice.kind}")

    base_sig = signal_for_choice(data5, pretest5, test5, choice, future=5)

    fee_perfs = [perf_from_signal(test5, base_sig, fee) for fee in FEES]
    fee_positive = float(np.mean([p.ret > 0 for p in fee_perfs]))
    fee_median_ret = float(np.median([p.ret for p in fee_perfs]))
    fee_worst_mdd = float(np.min([p.mdd for p in fee_perfs]))
    fee_min_pf = float(np.min([finite_pf(p.pf) for p in fee_perfs]))
    fee_min_trades = int(np.min([p.trades for p in fee_perfs]))

    neighbor_perfs = []
    for params in nearby_params(choice.kind, choice.params):
        sig = fixed_signal(data5, pretest5, test5, choice.kind, params)
        neighbor_perfs.append(perf_from_signal(test5, sig, STRESS_FEE))
    neighbor_positive = float(np.mean([p.ret > 0 for p in neighbor_perfs]))
    neighbor_median_ret = float(np.median([p.ret for p in neighbor_perfs]))
    neighbor_worst_mdd = float(np.min([p.mdd for p in neighbor_perfs]))

    raw10, bench10 = dl(ticker, "10y"), dl(benchmark, "10y")
    data10 = make_features(raw10, bench10, future=5, target_pct=.01)
    hist_positive, hist_median_ret, hist_worst_mdd, hist_trades = history_stress(data10, choice.kind, choice.params, future=5)

    reasons = []
    if fee_positive < 1.0: reasons.append("비용스트레스")
    if fee_median_ret <= 0: reasons.append("비용수익")
    if fee_worst_mdd < -0.25: reasons.append("비용MDD")
    if fee_min_pf < 1.05: reasons.append("비용PF")
    if fee_min_trades < 5: reasons.append("거래수")
    if neighbor_positive < 0.60: reasons.append("파라미터민감")
    if neighbor_median_ret <= 0: reasons.append("파라미터수익")
    if neighbor_worst_mdd < -0.25: reasons.append("파라미터MDD")
    if hist_positive < 0.50: reasons.append("10년구간안정")
    if hist_median_ret <= 0: reasons.append("10년중앙수익")
    if hist_worst_mdd < -0.30: reasons.append("10년MDD")
    if hist_trades < 12: reasons.append("10년거래수")

    confirmed = len(reasons) == 0
    return {
        "2차통과": "✅" if confirmed else "❌",
        "2차등급": "확인후보" if confirmed else "보류",
        "종목": row["종목"],
        "코드": ticker,
        "시장": market,
        "전략": choice.kind,
        "전략파라미터": json.dumps(choice.params, ensure_ascii=False, sort_keys=True),
        "1차등급": row["최종등급"],
        "1차TEST수익": float(row["TEST수익"]),
        "1차q": float(row["다중검정q"]) if np.isfinite(row["다중검정q"]) else np.nan,
        "비용양수비율": fee_positive,
        "비용중앙수익": fee_median_ret,
        "비용최악MDD": fee_worst_mdd,
        "비용최소PF": fee_min_pf,
        "비용최소거래수": fee_min_trades,
        "파라미터양수비율": neighbor_positive,
        "파라미터중앙수익": neighbor_median_ret,
        "파라미터최악MDD": neighbor_worst_mdd,
        "10년양수비율": hist_positive,
        "10년중앙수익": hist_median_ret,
        "10년최악MDD": hist_worst_mdd,
        "10년거래수": hist_trades,
        "보류사유": "-" if confirmed else ", ".join(reasons),
        "확인엔진": ENGINE_VERSION,
    }


def main():
    Path("reports").mkdir(exist_ok=True)
    if not REPORT.exists():
        pd.DataFrame().to_csv(OUT, index=False)
        SUMMARY.write_text("# APEX stress confirmation\n\n- primary report missing\n", encoding="utf-8")
        return

    primary = pd.read_csv(REPORT)
    if primary.empty:
        pd.DataFrame().to_csv(OUT, index=False)
        SUMMARY.write_text("# APEX stress confirmation\n\n- no primary rows\n", encoding="utf-8")
        return

    mask = primary["최종등급"].isin(["A", "B", "관찰"])
    candidates = primary.loc[mask].copy()
    rows, errors = [], []
    for _, row in candidates.iterrows():
        try:
            rows.append(confirm_one(row))
        except Exception as e:
            errors.append({"종목": row.get("종목"), "코드": row.get("코드"), "오류": repr(e)})

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values(["2차통과", "비용중앙수익"], ascending=[False, False]).reset_index(drop=True)
    result.to_csv(OUT, index=False, encoding="utf-8-sig")

    confirmed = result[result["2차통과"] == "✅"] if not result.empty else result
    lines = [
        "# APEX stress confirmation",
        "",
        f"- engine: {ENGINE_VERSION}",
        f"- candidates from primary scan: {len(candidates)}",
        f"- confirmed: {len(confirmed)}",
        f"- errors: {len(errors)}",
        "",
    ]
    if not result.empty:
        lines += ["## Results", ""]
        for _, r in result.iterrows():
            lines.append(
                f"- {r['2차등급']} {r['종목']} ({r['코드']}): {r['전략']}, "
                f"cost_med={r['비용중앙수익']:.2%}, neighbor_pos={r['파라미터양수비율']:.0%}, "
                f"10y_pos={r['10년양수비율']:.0%}, reason={r['보류사유']}"
            )
    if errors:
        lines += ["", "## Errors", "", "```json", json.dumps(errors, ensure_ascii=False, indent=2), "```"]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
