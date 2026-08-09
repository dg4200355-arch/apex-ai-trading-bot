"""Autonomous real-market validation runner.

Scans one rotating half of the Korea+US 40-stock universes (20 KR + 20 US per run),
applies Benjamini-Hochberg multiple-testing control, and writes CSV/Markdown reports.
Adjacent weekday runs cover the other half, so the full 80-stock universe is revisited
roughly every two scan days. No live orders are placed.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import numpy as np
import pandas as pd
import yfinance as yf

from engine import analyze_frame, make_features, run_self_tests

ENGINE_VERSION = "8.2-next-open"
KST = timezone(timedelta(hours=9))

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


def dl(ticker: str, period: str = "5y") -> pd.DataFrame:
    d = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
    if d is None or d.empty:
        raise RuntimeError(f"no data: {ticker}")
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    return d[["Open", "High", "Low", "Close", "Volume"]].dropna()


def bh_qvalues(values):
    p = np.asarray(values, dtype=float)
    q = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    if not valid.any():
        return q
    pv = p[valid]
    order = np.argsort(pv)
    ranked = pv[order]
    m = len(ranked)
    raw = ranked * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(raw[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.clip(adj, 0, 1)
    q[np.where(valid)[0]] = out
    return q


def apply_portfolio_control(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["다중검정q"] = bh_qvalues(out["타이밍p"].to_numpy())
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
    return out


def selected_half(items, cohort: int):
    midpoint = len(items) // 2
    return items[:midpoint] if cohort == 0 else items[midpoint:]


def main():
    checks = run_self_tests()
    if not checks or not all(checks.values()):
        raise SystemExit(f"self-tests failed: {checks}")

    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    now_kst = now_utc.astimezone(KST)
    cohort = now_kst.toordinal() % 2
    cohort_label = "A" if cohort == 0 else "B"
    run_at = now_utc.isoformat()

    kr_items = selected_half(list(KOREA.items()), cohort)
    us_items = selected_half(list(USA.items()), cohort)
    cases = [("KR", name, ticker, "^KS11") for name, ticker in kr_items]
    cases += [("US", name, ticker, "SPY") for name, ticker in us_items]

    markets = {"^KS11": dl("^KS11"), "SPY": dl("SPY")}
    rows, errors = [], []
    for market_name, name, ticker, benchmark in cases:
        try:
            raw = dl(ticker)
            data = make_features(raw, markets[benchmark], future=5, target_pct=.01)
            result = analyze_frame(name, ticker, data, future=5, fee=.0015, fast_mode=True)
            result["시장"] = market_name
            result["실행시각UTC"] = run_at
            result["엔진버전"] = ENGINE_VERSION
            result["코호트"] = cohort_label
            rows.append(result)
            print(ticker, result.get("등급"), result.get("선택전략"), result.get("TEST수익"), result.get("탈락사유"))
        except Exception as e:
            errors.append({"시장": market_name, "종목": name, "코드": ticker, "오류": repr(e), "실행시각UTC": run_at, "엔진버전": ENGINE_VERSION, "코호트": cohort_label})
            print(ticker, "ERROR", repr(e))

    if not rows:
        raise SystemExit("no analyzable market rows")

    result = apply_portfolio_control(pd.DataFrame(rows))
    result = result.sort_values(["최종통과", "점수"], ascending=[True, False]).reset_index(drop=True)

    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)
    result.to_csv(out_dir / "latest_validation.csv", index=False, encoding="utf-8-sig")
    (out_dir / "latest_errors.json").write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")

    strict = result[result["최종통과"] == "✅"]
    watch = result[result["최종등급"].isin(["A", "B", "관찰"])]
    lines = [
        "# APEX autonomous validation summary",
        "",
        f"- engine_version: {ENGINE_VERSION}",
        f"- cohort: {cohort_label}",
        f"- run_at_utc: {run_at}",
        f"- analyzed: {len(result)}",
        f"- A-grade passed: {len(strict)}",
        f"- watch-or-better: {len(watch)}",
        f"- data/errors: {len(errors)}",
        "",
        "## Top candidates",
        "",
    ]
    for _, r in result.head(12).iterrows():
        pf = r["PF"] if np.isfinite(r["PF"]) else float("nan")
        tp = r["타이밍p"] if np.isfinite(r["타이밍p"]) else float("nan")
        qv = r["다중검정q"] if np.isfinite(r["다중검정q"]) else float("nan")
        lines.append(
            f"- {r['최종등급']} {r['종목']} ({r['코드']}): strategy={r['선택전략']}, "
            f"TEST={r['TEST수익']:.2%}, PF={pf:.2f}, timing_p={tp:.3f}, q={qv:.3f}"
        )
    (out_dir / "latest_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
