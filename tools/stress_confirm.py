"""Second-stage robustness confirmation with immutable stage-1 choices.

Stage 2 is rejection-only. It NEVER re-selects a strategy or parameter. It reads
stage 1's exact strategy family, exact JSON parameters, and exact market-data
cutoff, reconstructs the same test, checks reproducibility, and only then tries to
break the frozen strategy with higher costs, nearby parameter perturbations, and a
10-year historical regime stress ending at the same cutoff.

No live orders are placed.
"""
from __future__ import annotations

from pathlib import Path
import json
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from engine import build_rule_signal, fit_ai_predict, make_features, perf_from_signal

REPORT = Path("reports/latest_validation.csv")
OUT = Path("reports/latest_confirmation.csv")
SUMMARY = Path("reports/latest_confirmation.md")
BASE_FEE = 0.0015
STRESS_FEE = 0.0025
FEES = [0.0015, 0.0025, 0.0035]
FUTURE = 5
TARGET_PCT = 0.01
REPRO_TOL = 0.01
ENGINE_VERSION = "8.5-frozen-confirm"


def dl_dates(ticker: str, start: pd.Timestamp, cutoff: pd.Timestamp) -> pd.DataFrame:
    end = cutoff + pd.Timedelta(days=1)
    d = yf.download(
        ticker,
        start=start.date().isoformat(),
        end=end.date().isoformat(),
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    if d is None or d.empty:
        raise RuntimeError(f"no data: {ticker}")
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    need = ["Open", "High", "Low", "Close", "Volume"]
    if any(c not in d.columns for c in need):
        raise RuntimeError(f"bad OHLCV: {ticker}")
    d = d[need].dropna().sort_index()
    return d.loc[d.index <= cutoff]


def parse_frozen_choice(row: pd.Series) -> Tuple[str, Dict[str, float], pd.Timestamp, pd.Timestamp]:
    required = ["선택전략", "전략파라미터", "데이터시작일", "데이터기준일"]
    missing = [c for c in required if c not in row.index or pd.isna(row[c])]
    if missing:
        raise ValueError(f"primary freeze metadata missing: {missing}")
    kind = str(row["선택전략"])
    params = json.loads(str(row["전략파라미터"]))
    if not isinstance(params, dict) or not params:
        raise ValueError("invalid frozen strategy parameters")
    start = pd.Timestamp(str(row["데이터시작일"]))
    cutoff = pd.Timestamp(str(row["데이터기준일"]))
    if start >= cutoff:
        raise ValueError("invalid primary data window")
    return kind, params, start, cutoff


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
    else:
        raise ValueError(f"unknown frozen strategy: {kind}")
    unique, seen = [], set()
    for p in out:
        key = json.dumps(p, sort_keys=True)
        if key not in seen:
            unique.append(p); seen.add(key)
    return unique


def fixed_signal(data: pd.DataFrame, pretest: pd.DataFrame, target: pd.DataFrame, kind: str, params: Dict[str, float]) -> pd.Series:
    if kind == "AI":
        if len(pretest) < 450 or pretest["target"].nunique() < 2:
            raise ValueError("frozen AI training window unavailable")
        p = fit_ai_predict(pretest, target, True)
        return (
            (pd.Series(p, index=target.index) >= float(params["threshold"]))
            & (target["Close"] > target["ema55"])
            & target["rsi"].between(45, 78)
        )
    return build_rule_signal(data, kind, params).reindex(target.index).fillna(False)


def history_stress(data10: pd.DataFrame, kind: str, params: Dict[str, float]) -> Tuple[float, float, float, int]:
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
            train_end = max(0, a - FUTURE)
            train = data10.iloc[:train_end].copy()
            if len(train) < 450 or train["target"].nunique() < 2:
                continue
        else:
            train = data10.iloc[:a].copy()
        sig = fixed_signal(data10, train, target, kind, params)
        perf = perf_from_signal(target, sig, STRESS_FEE)
        rets.append(perf.ret)
        mdds.append(perf.mdd)
        trades += perf.trades
    if not rets:
        return 0.0, -1.0, -1.0, 0
    return float(np.mean(np.array(rets) > 0)), float(np.median(rets)), float(np.min(mdds)), int(trades)


def finite_pf(x: float) -> float:
    return float(x) if np.isfinite(x) else 99.0


def confirm_one(row: pd.Series) -> Dict[str, object]:
    ticker = str(row["코드"])
    market = str(row["시장"])
    benchmark = "^KS11" if market == "KR" else "SPY"
    kind, params, start5, cutoff = parse_frozen_choice(row)

    raw5 = dl_dates(ticker, start5, cutoff)
    bench5 = dl_dates(benchmark, start5, cutoff)
    data5 = make_features(raw5, bench5, future=FUTURE, target_pct=TARGET_PCT)
    if len(data5) < 850:
        raise ValueError("frozen 5y data insufficient")
    split = int(len(data5) * 0.75)
    pretest5 = data5.iloc[:split].copy()
    test5 = data5.iloc[split:].copy()
    base_sig = fixed_signal(data5, pretest5, test5, kind, params)
    base_perf = perf_from_signal(test5, base_sig, BASE_FEE)
    primary_ret = float(row["TEST수익"])
    repro_error = abs(float(base_perf.ret) - primary_ret)

    fee_perfs = [perf_from_signal(test5, base_sig, fee) for fee in FEES]
    fee_positive = float(np.mean([p.ret > 0 for p in fee_perfs]))
    fee_median_ret = float(np.median([p.ret for p in fee_perfs]))
    fee_worst_mdd = float(np.min([p.mdd for p in fee_perfs]))
    fee_min_pf = float(np.min([finite_pf(p.pf) for p in fee_perfs]))
    fee_min_trades = int(np.min([p.trades for p in fee_perfs]))

    neighbor_perfs = []
    for pset in nearby_params(kind, params):
        sig = fixed_signal(data5, pretest5, test5, kind, pset)
        neighbor_perfs.append(perf_from_signal(test5, sig, STRESS_FEE))
    neighbor_positive = float(np.mean([p.ret > 0 for p in neighbor_perfs]))
    neighbor_median_ret = float(np.median([p.ret for p in neighbor_perfs]))
    neighbor_worst_mdd = float(np.min([p.mdd for p in neighbor_perfs]))

    start10 = cutoff - pd.DateOffset(years=10)
    raw10 = dl_dates(ticker, start10, cutoff)
    bench10 = dl_dates(benchmark, start10, cutoff)
    data10 = make_features(raw10, bench10, future=FUTURE, target_pct=TARGET_PCT)
    hist_positive, hist_median_ret, hist_worst_mdd, hist_trades = history_stress(data10, kind, params)

    reasons = []
    if repro_error > REPRO_TOL: reasons.append("1차재현오차")
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
        "전략": kind,
        "전략파라미터": json.dumps(params, ensure_ascii=False, sort_keys=True),
        "1차데이터기준일": cutoff.date().isoformat(),
        "1차등급": row["최종등급"],
        "1차TEST수익": primary_ret,
        "재현TEST수익": float(base_perf.ret),
        "재현오차": repro_error,
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
        SUMMARY.write_text("# APEX frozen stress confirmation\n\n- primary report missing\n", encoding="utf-8")
        return

    primary = pd.read_csv(REPORT)
    if primary.empty:
        pd.DataFrame().to_csv(OUT, index=False)
        SUMMARY.write_text("# APEX frozen stress confirmation\n\n- no primary rows\n", encoding="utf-8")
        return

    freeze_cols = {"전략파라미터", "데이터시작일", "데이터기준일"}
    if not freeze_cols.issubset(primary.columns):
        raise SystemExit(f"primary report predates frozen schema: {sorted(freeze_cols - set(primary.columns))}")

    candidates = primary.loc[primary["최종등급"].isin(["A", "B", "관찰"])].copy()
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
        "# APEX frozen stress confirmation", "",
        f"- engine: {ENGINE_VERSION}",
        f"- candidates from primary scan: {len(candidates)}",
        f"- confirmed: {len(confirmed)}",
        f"- errors: {len(errors)}", "",
    ]
    if not result.empty:
        lines += ["## Results", ""]
        for _, r in result.iterrows():
            lines.append(
                f"- {r['2차등급']} {r['종목']} ({r['코드']}): {r['전략']} {r['전략파라미터']}, "
                f"repro_error={r['재현오차']:.4f}, cost_med={r['비용중앙수익']:.2%}, "
                f"neighbor_pos={r['파라미터양수비율']:.0%}, 10y_pos={r['10년양수비율']:.0%}, reason={r['보류사유']}"
            )
    if errors:
        lines += ["", "## Errors", "", "```json", json.dumps(errors, ensure_ascii=False, indent=2), "```"]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
