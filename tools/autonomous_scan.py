"""Autonomous real-market validation runner.

Runs a compact Korea+US universe with the same validation engine, applies
Benjamini-Hochberg multiple-testing control, and writes CSV/Markdown artifacts.
No live orders are placed. A run with zero A-grade candidates is valid.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import numpy as np
import pandas as pd
import yfinance as yf

from engine import analyze_frame, make_features, run_self_tests

ENGINE_VERSION = "8.2-next-open"

KOREA = {
    "삼성전자":"005930.KS",
    "SK하이닉스":"000660.KS",
    "NAVER":"035420.KS",
    "셀트리온":"068270.KS",
    "현대차":"005380.KS",
    "한화에어로스페이스":"012450.KS",
}
USA = {
    "Apple":"AAPL",
    "Microsoft":"MSFT",
    "NVIDIA":"NVDA",
    "Amazon":"AMZN",
    "Meta":"META",
    "Broadcom":"AVGO",
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


def main():
    checks = run_self_tests()
    if not checks or not all(checks.values()):
        raise SystemExit(f"self-tests failed: {checks}")

    run_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    cases = []
    for name, ticker in KOREA.items():
        cases.append(("KR", name, ticker, "^KS11"))
    for name, ticker in USA.items():
        cases.append(("US", name, ticker, "SPY"))

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
            rows.append(result)
            print(ticker, result.get("등급"), result.get("선택전략"), result.get("TEST수익"), result.get("탈락사유"))
        except Exception as e:
            errors.append({"시장": market_name, "종목": name, "코드": ticker, "오류": repr(e), "실행시각UTC": run_at, "엔진버전": ENGINE_VERSION})
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
        f"- run_at_utc: {run_at}",
        f"- analyzed: {len(result)}",
        f"- A-grade passed: {len(strict)}",
        f"- watch-or-better: {len(watch)}",
        f"- data/errors: {len(errors)}",
        "",
        "## Top candidates",
        "",
    ]
    for _, r in result.head(10).iterrows():
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
