"""Portfolio concentration gate for forward-validated candidates.

Individual validation is not enough for portfolio use: highly correlated candidates
can duplicate the same risk. Recent daily-return correlations define risk clusters.
If multiple members of the same cluster eventually become forward-validated, one
cluster leader is selected deterministically from forward evidence and the others
are blocked as duplicates. This stage never places orders.
"""
from __future__ import annotations

from pathlib import Path
import json
from typing import Dict, List, Set

import numpy as np
import pandas as pd

from market_data import download_ohlcv

STATE = Path("reports/paper_state.json")
PROMOTION = Path("reports/promotion_status.csv")
OUT = Path("reports/portfolio_risk.csv")
SUMMARY = Path("reports/portfolio_risk.md")
VERSION = "portfolio-gate-1.1-cluster-leader"
CORR_LIMIT = 0.80
MIN_COMMON_DAYS = 120


def load_state() -> Dict[str, dict]:
    if not STATE.exists():
        return {}
    try:
        obj = json.loads(STATE.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def load_promotion() -> pd.DataFrame:
    if not PROMOTION.exists() or not PROMOTION.stat().st_size:
        return pd.DataFrame()
    try:
        return pd.read_csv(PROMOTION)
    except Exception:
        return pd.DataFrame()


def pairwise_correlations(state: Dict[str, dict]):
    returns, errors = {}, {}
    for ticker in state:
        try:
            d = download_ohlcv(ticker, period="1y")
            r = d["Close"].pct_change().dropna().rename(ticker)
            if len(r) < MIN_COMMON_DAYS:
                raise ValueError(f"insufficient correlation history: {len(r)}")
            returns[ticker] = r
        except Exception as e:
            errors[ticker] = repr(e)
    pairs = []
    tickers = list(returns)
    for i, a in enumerate(tickers):
        for b in tickers[i + 1:]:
            if str(state[a].get("시장")) != str(state[b].get("시장")):
                continue
            x = pd.concat([returns[a], returns[b]], axis=1, join="inner").dropna()
            if len(x) < MIN_COMMON_DAYS:
                continue
            corr = float(x.iloc[:, 0].corr(x.iloc[:, 1]))
            if np.isfinite(corr):
                pairs.append((a, b, corr, len(x)))
    return pairs, errors


def correlation_components(tickers: List[str], pairs):
    graph: Dict[str, Set[str]] = {t: set() for t in tickers}
    for a, b, corr, _ in pairs:
        if corr >= CORR_LIMIT:
            graph[a].add(b); graph[b].add(a)
    components, seen = [], set()
    for t in tickers:
        if t in seen:
            continue
        stack, comp = [t], []
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x); stack.extend(graph[x] - seen)
        components.append(sorted(comp))
    return components


def _finite(v, fallback):
    try:
        x = float(v)
        return x if np.isfinite(x) else fallback
    except Exception:
        return fallback


def evidence_rank(row: pd.Series):
    """Lexicographic leader rank; higher tuple is better.

    No historical/backtest result is used here. Only forward evidence from the
    promotion gate decides among candidates that already passed individual forward
    validation.
    """
    return (
        _finite(row.get("전진누적수익"), -np.inf),
        _finite(row.get("부트스트랩양수확률"), -np.inf),
        min(_finite(row.get("PF"), -np.inf), 10.0),
        _finite(row.get("전진MDD"), -np.inf),
        _finite(row.get("완료거래"), -np.inf),
        str(row.get("코드", "")),
    )


def choose_cluster_leaders(components, promo_map):
    leaders = {}
    for comp in components:
        eligible = []
        for ticker in comp:
            row = promo_map.get(ticker, pd.Series(dtype=object))
            if not len(row):
                continue
            if str(row.get("최종상태")) != "전진검증완료":
                continue
            if str(row.get("동결검증")) != "FROZEN_VERIFIED":
                continue
            eligible.append((evidence_rank(row), ticker))
        if eligible:
            eligible.sort(reverse=True)
            leader = eligible[0][1]
            for ticker in comp:
                leaders[ticker] = leader
    return leaders


def main():
    Path("reports").mkdir(exist_ok=True)
    state = load_state()
    promotion = load_promotion()
    if not state:
        pd.DataFrame().to_csv(OUT, index=False, encoding="utf-8-sig")
        SUMMARY.write_text(f"# APEX portfolio gate\n\n- gate: {VERSION}\n- no tracked candidates\n", encoding="utf-8")
        return

    promo_map = {}
    if not promotion.empty and "코드" in promotion.columns:
        promo_map = {str(r["코드"]): r for _, r in promotion.iterrows()}

    pairs, errors = pairwise_correlations(state)
    components = correlation_components(list(state), pairs)
    cluster_of = {}
    for idx, comp in enumerate(components, start=1):
        for ticker in comp:
            cluster_of[ticker] = f"C{idx}"
    leaders = choose_cluster_leaders(components, promo_map)

    max_peer = {t: (None, np.nan, 0) for t in state}
    for a, b, corr, n in pairs:
        if not np.isfinite(max_peer[a][1]) or corr > max_peer[a][1]: max_peer[a] = (b, corr, n)
        if not np.isfinite(max_peer[b][1]) or corr > max_peer[b][1]: max_peer[b] = (a, corr, n)

    rows = []
    for ticker, s in state.items():
        promo = promo_map.get(ticker, pd.Series(dtype=object))
        final_status = str(promo.get("최종상태", "관찰중")) if len(promo) else "관찰중"
        verified = str(promo.get("동결검증", "LEGACY_LOCKED")) if len(promo) else ("FROZEN_VERIFIED" if s.get("frozen_verified") else "LEGACY_LOCKED")
        peer, corr, common = max_peer[ticker]
        peer_name = state.get(peer, {}).get("종목", peer) if peer else "-"
        high_corr = bool(np.isfinite(corr) and corr >= CORR_LIMIT)
        data_error = errors.get(ticker)
        leader = leaders.get(ticker)
        is_leader = leader == ticker
        leader_name = state.get(leader, {}).get("종목", leader) if leader else "-"

        reasons = []
        if verified != "FROZEN_VERIFIED": reasons.append("동결재검증")
        if final_status != "전진검증완료": reasons.append("전진검증")
        if data_error: reasons.append("상관데이터")
        if final_status == "전진검증완료" and leader and not is_leader:
            reasons.append("고상관군집비대표")
        allowed = len(reasons) == 0

        rows.append({
            "포트폴리오허용": "✅" if allowed else "❌",
            "최종상태": final_status,
            "동결검증": verified,
            "종목": s.get("종목", ticker),
            "코드": ticker,
            "시장": s.get("시장", "?"),
            "전략": s.get("전략", "?"),
            "상관군집": cluster_of.get(ticker, "-"),
            "군집대표": "⭐" if is_leader else "-",
            "군집대표종목": leader_name,
            "최대상관": corr,
            "최대상관대상": peer_name,
            "공통거래일": common,
            "중복위험": "⚠️" if high_corr else "-",
            "포트폴리오대기조건": "-" if allowed else ", ".join(reasons),
            "데이터오류": data_error or "-",
            "게이트": VERSION,
        })

    result = pd.DataFrame(rows)
    result.to_csv(OUT, index=False, encoding="utf-8-sig")
    allowed = result[result["포트폴리오허용"] == "✅"]
    high = result[result["중복위험"] == "⚠️"]
    lines = [
        "# APEX portfolio concentration gate", "",
        f"- gate: {VERSION}",
        f"- tracked: {len(result)}",
        f"- portfolio-allowed: {len(allowed)}",
        f"- high-correlation candidates: {len(high)}", "",
        f"Correlation warning threshold: {CORR_LIMIT:.2f} using at least {MIN_COMMON_DAYS} common daily returns.",
        "If several members of one high-correlation cluster become individually forward-validated, exactly one leader is selected using forward evidence only.",
        "This stage never places orders.", "",
        "## Status", "",
    ]
    for _, r in result.iterrows():
        corr = r["최대상관"]
        corr_txt = "-" if not np.isfinite(corr) else f"{corr:.3f}"
        lines.append(
            f"- {r['종목']} ({r['코드']}): cluster={r['상관군집']}, leader={r['군집대표종목']}, "
            f"max_corr={corr_txt} vs {r['최대상관대상']}, risk={r['중복위험']}, "
            f"allowed={r['포트폴리오허용']}, waiting={r['포트폴리오대기조건']}"
        )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
