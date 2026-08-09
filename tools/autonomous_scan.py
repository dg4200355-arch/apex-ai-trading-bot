"""Autonomous real-market validation runner.

Every scheduled run scans 40 Korea + 40 US stocks. Global BH correction uses all
80 hypotheses. Stable-strategy absence is a normal rejection, while true data or
engine faults fail the run closed so stale known-good reports remain authoritative.
Data repair diagnostics are recorded per row. No live orders are placed.
"""
from datetime import datetime, timezone
from pathlib import Path
import json

import numpy as np
import pandas as pd

from engine import analyze_frame, make_features, run_self_tests, select_ai, select_rule, split_holdout
from market_data import download_ohlcv

ENGINE_VERSION = "8.5-frozen-primary"
FAMILY_SIZE = 80
BASE_FEE = 0.0015
FUTURE = 5
TARGET_PCT = 0.01
FAILURE_REPORT = Path("reports/failed_scan_errors.json")

KOREA = {
    "삼성전자":"005930.KS","SK하이닉스":"000660.KS","현대차":"005380.KS","기아":"000270.KS",
    "NAVER":"035420.KS","카카오":"035720.KS","삼성바이오로직스":"207940.KS","셀트리온":"068270.KS",
    "LG에너지솔루션":"373220.KS","POSCO홀딩스":"005490.KS","한화에어로스페이스":"012450.KS","HD현대중공업":"329180.KS",
    "KB금융":"105560.KS","신한지주":"055550.KS","하나금융지주":"086790.KS","우리금융지주":"316140.KS",
    "삼성물산":"028260.KS","삼성SDI":"006400.KS","LG화학":"051910.KS","LG전자":"066570.KS",
    "SK이노베이션":"096770.KS","SK텔레콤":"017670.KS","KT":"030200.KS","한국전력":"015760.KS",
    "두산에너빌리티":"034020.KS","현대로템":"064350.KS","한화오션":"042660.KS","대한항공":"003490.KS",
    "아모레퍼시픽":"090430.KS","KT&G":"033780.KS","삼성전기":"009150.KS","LG이노텍":"011070.KS",
    "삼성중공업":"010140.KS","기업은행":"024110.KS","포스코퓨처엠":"003670.KS","에코프로비엠":"247540.KQ",
    "에코프로":"086520.KQ","알테오젠":"196170.KQ","HLB":"028300.KQ","리노공업":"058470.KQ"
}
USA = {
    "Apple":"AAPL","Microsoft":"MSFT","NVIDIA":"NVDA","Amazon":"AMZN","Meta":"META","Alphabet":"GOOGL",
    "Tesla":"TSLA","Broadcom":"AVGO","AMD":"AMD","Netflix":"NFLX","JPMorgan":"JPM","Eli Lilly":"LLY",
    "Berkshire":"BRK-B","Visa":"V","Mastercard":"MA","Walmart":"WMT","Costco":"COST","Oracle":"ORCL",
    "Salesforce":"CRM","Adobe":"ADBE","Palantir":"PLTR","Micron":"MU","Qualcomm":"QCOM","Intel":"INTC",
    "Cisco":"CSCO","IBM":"IBM","Coca-Cola":"KO","PepsiCo":"PEP","McDonalds":"MCD","Nike":"NKE",
    "ExxonMobil":"XOM","Chevron":"CVX","UnitedHealth":"UNH","Johnson&Johnson":"JNJ","Merck":"MRK","AbbVie":"ABBV",
    "HomeDepot":"HD","Boeing":"BA","Caterpillar":"CAT","GoldmanSachs":"GS"
}

NORMAL_REJECTION_MESSAGES = {
    "안정적인 후보 전략 없음",
    "데이터 부족",
    "학습 구간 부족",
    "최종 검증 구간 부족",
}


def dl(ticker: str, period: str = "5y") -> pd.DataFrame:
    return download_ohlcv(ticker, period=period)


def bh_qvalues(values, family_size: int = FAMILY_SIZE):
    p = np.asarray(values, dtype=float)
    q = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    if not valid.any():
        return q
    pv = p[valid]
    order = np.argsort(pv)
    ranked = pv[order]
    m = max(int(family_size), len(ranked))
    raw = ranked * m / np.arange(1, len(ranked) + 1)
    adj = np.minimum.accumulate(raw[::-1])[::-1]
    out = np.empty(len(ranked))
    out[order] = np.clip(adj, 0, 1)
    q[np.where(valid)[0]] = out
    return q


def apply_portfolio_control(df: pd.DataFrame, family_size: int = FAMILY_SIZE) -> pd.DataFrame:
    out = df.copy()
    out["다중검정q"] = bh_qvalues(out["타이밍p"].to_numpy(), family_size)
    final_grade, final_pass = [], []
    for _, row in out.iterrows():
        grade, q = row["등급"], row["다중검정q"]
        if grade == "A" and np.isfinite(q) and q <= 0.20:
            g, ok = "A", True
        elif grade in {"A", "B"}:
            g, ok = "B", False
        elif grade == "관찰":
            g, ok = "관찰", False
        else:
            g, ok = "탈락", False
        final_grade.append(g)
        final_pass.append("✅" if ok else "❌")
    out["최종등급"] = final_grade
    out["최종통과"] = final_pass
    out["검정패밀리"] = family_size
    out["스캔모드"] = "FULL80"
    return out


def freeze_selected_choice(data: pd.DataFrame, expected_kind: str):
    """Recreate stage-1 selection with the exact same purged holdout boundary."""
    pretest, embargo, test = split_holdout(data, future=FUTURE, train_fraction=0.75)
    if len(embargo) != FUTURE:
        raise ValueError(f"freeze embargo mismatch: {len(embargo)} != {FUTURE}")
    if pretest.empty or test.empty:
        raise ValueError("cannot freeze strategy on empty purged split")
    rule = select_rule(pretest, data, BASE_FEE)
    ai = select_ai(pretest, FUTURE, BASE_FEE, True) if pretest["target"].nunique() > 1 else None
    choices = [c for c in (rule, ai) if c is not None]
    if not choices:
        raise ValueError("cannot freeze selected strategy")
    choice = max(choices, key=lambda c: c.validation_score)
    if choice.kind != expected_kind:
        raise ValueError(f"selection mismatch: analyze={expected_kind}, freeze={choice.kind}")
    return choice


def normal_rejection_row(name: str, ticker: str, reason: str) -> dict:
    return {
        "통과": "❌", "등급": "탈락", "종목": name, "코드": ticker, "선택전략": "없음",
        "사전중앙수익": np.nan, "사전양수비율": np.nan, "TEST수익": np.nan,
        "TEST구간양수비율": np.nan, "TEST구간중앙수익": np.nan, "타이밍p": 1.0,
        "최근63일": np.nan, "매수보유": np.nan, "MDD": np.nan, "TEST거래수": 0,
        "승률": np.nan, "PF": np.nan, "샤프": np.nan, "AI OOF AUC": np.nan,
        "AI TEST AUC": np.nan, "학습끝일": "-", "TEST시작일": "-", "Embargo거래일": FUTURE,
        "탈락사유": reason, "점수": -999.0,
        "전략파라미터": "{}", "전략검증점수": np.nan,
    }


def fail_closed(errors: list, run_at: str):
    """Transient/engine faults must not become evidence that removes candidates."""
    if not errors:
        if FAILURE_REPORT.exists():
            FAILURE_REPORT.unlink()
        return
    FAILURE_REPORT.parent.mkdir(exist_ok=True)
    FAILURE_REPORT.write_text(
        json.dumps({"run_at_utc": run_at, "engine": ENGINE_VERSION, "errors": errors}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    raise SystemExit(f"FULL80 failed closed: {len(errors)} true data/engine errors; prior good report preserved")


def main():
    checks = run_self_tests()
    if not checks or not all(checks.values()):
        raise SystemExit(f"self-tests failed: {checks}")

    run_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    cases = [("KR", name, ticker, "^KS11") for name, ticker in KOREA.items()]
    cases += [("US", name, ticker, "SPY") for name, ticker in USA.items()]
    if len(cases) != FAMILY_SIZE:
        raise SystemExit(f"universe size mismatch: {len(cases)} != {FAMILY_SIZE}")

    markets = {"^KS11": dl("^KS11"), "SPY": dl("SPY")}
    rows, errors = [], []
    for market_name, name, ticker, benchmark in cases:
        try:
            raw = dl(ticker)
            repaired = int(raw.attrs.get("ohlcv_repaired_bars", 0))
            max_repair = float(raw.attrs.get("ohlcv_max_repair_pct", 0.0))
            data = make_features(raw, markets[benchmark], future=FUTURE, target_pct=TARGET_PCT)
            try:
                result = analyze_frame(name, ticker, data, future=FUTURE, fee=BASE_FEE, fast_mode=True)
            except ValueError as e:
                reason = str(e)
                if reason not in NORMAL_REJECTION_MESSAGES:
                    raise
                result = normal_rejection_row(name, ticker, reason)

            if result["선택전략"] != "없음":
                choice = freeze_selected_choice(data, str(result["선택전략"]))
                result["전략파라미터"] = json.dumps(choice.params, ensure_ascii=False, sort_keys=True)
                result["전략검증점수"] = float(choice.validation_score)

            result["데이터시작일"] = pd.Timestamp(raw.index[0]).date().isoformat()
            result["데이터기준일"] = pd.Timestamp(raw.index[-1]).date().isoformat()
            result["데이터행수"] = int(len(raw))
            result["OHLC보정봉수"] = repaired
            result["OHLC최대보정폭"] = max_repair
            result["시장"] = market_name
            result["실행시각UTC"] = run_at
            result["엔진버전"] = ENGINE_VERSION
            rows.append(result)
            print(ticker, result.get("등급"), result.get("선택전략"), f"repairs={repaired}", result.get("TEST수익"))
        except Exception as e:
            errors.append({
                "시장": market_name, "종목": name, "코드": ticker, "오류": repr(e),
                "실행시각UTC": run_at, "엔진버전": ENGINE_VERSION,
            })
            print(ticker, "ERROR", repr(e))

    fail_closed(errors, run_at)
    if not rows:
        raise SystemExit("no analyzable market rows")

    result = apply_portfolio_control(pd.DataFrame(rows), FAMILY_SIZE)
    result = result.sort_values("점수", ascending=False).reset_index(drop=True)

    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)
    result.to_csv(out_dir / "latest_validation.csv", index=False, encoding="utf-8-sig")
    (out_dir / "latest_errors.json").write_text("[]", encoding="utf-8")

    strict = result[result["최종통과"] == "✅"]
    watch = result[result["최종등급"].isin(["A", "B", "관찰"])]
    normal_rejects = int((result["선택전략"] == "없음").sum())
    repaired_rows = int((pd.to_numeric(result["OHLC보정봉수"], errors="coerce").fillna(0) > 0).sum())
    total_repairs = int(pd.to_numeric(result["OHLC보정봉수"], errors="coerce").fillna(0).sum())
    lines = [
        "# APEX autonomous validation summary", "",
        f"- engine_version: {ENGINE_VERSION}", "- scan_mode: FULL80", f"- run_at_utc: {run_at}",
        f"- universe: {FAMILY_SIZE}", f"- result_rows: {len(result)}",
        f"- valid-data normal rejections: {normal_rejects}", "- true data/engine errors: 0",
        f"- tickers with isolated OHLC repairs: {repaired_rows}", f"- total repaired OHLC bars: {total_repairs}",
        f"- selection split: 75% boundary with {FUTURE}-bar purge/embargo",
        f"- A-grade passed after global correction: {len(strict)}", f"- watch-or-better: {len(watch)}", "",
        "## Top candidates", "",
    ]
    for _, r in result.head(15).iterrows():
        pf = r["PF"] if np.isfinite(r["PF"]) else float("nan")
        tp = r["타이밍p"] if np.isfinite(r["타이밍p"]) else float("nan")
        qv = r["다중검정q"] if np.isfinite(r["다중검정q"]) else float("nan")
        test_ret = r["TEST수익"] if np.isfinite(r["TEST수익"]) else float("nan")
        lines.append(
            f"- {r['최종등급']} {r['종목']} ({r['코드']}): strategy={r['선택전략']} {r['전략파라미터']}, "
            f"TEST={test_ret:.2%}, PF={pf:.2f}, timing_p={tp:.3f}, q80={qv:.3f}, "
            f"repairs={int(r['OHLC보정봉수'])}, embargo={int(r.get('Embargo거래일', FUTURE))}, data_end={r['데이터기준일']}"
        )
    (out_dir / "latest_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
