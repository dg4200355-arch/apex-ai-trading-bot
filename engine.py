from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = [
    "ret1", "ret3", "ret5", "ret10", "ema8_21", "ema21_55", "ema55_200",
    "rsi", "macd", "hist", "atr_pct", "bb_pos", "vol_ratio", "volatility",
    "range_pct", "market_ret5", "relative5",
]

@dataclass
class Perf:
    ret: float
    mdd: float
    trades: int
    winrate: float
    pf: float
    sharpe: float

@dataclass
class StrategyChoice:
    kind: str
    params: Dict[str, float]
    validation_score: float
    validation_median_return: float
    validation_positive_ratio: float
    validation_trades: int
    ai_oof_auc: float = np.nan


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    x = s.diff()
    gain = x.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-x.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return (100 - 100 / (1 + gain / loss.replace(0, np.nan))).fillna(50)


def atr(d: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = d["Close"].shift(1)
    tr = pd.concat(
        [d["High"] - d["Low"], (d["High"] - pc).abs(), (d["Low"] - pc).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def make_features(raw: pd.DataFrame, market: pd.DataFrame, future: int = 5, target_pct: float = 0.01) -> pd.DataFrame:
    d = raw[["Open", "High", "Low", "Close", "Volume"]].copy().sort_index()
    m = market["Close"].pct_change().rename("market_ret1")
    d = d.join(m, how="left").ffill()
    for n in [8, 20, 21, 55, 100, 200]:
        d[f"ema{n}"] = ema(d["Close"], n)
    d["rsi"] = rsi(d["Close"])
    macd = ema(d["Close"], 12) - ema(d["Close"], 26)
    sig = ema(macd, 9)
    d["macd"] = macd / d["Close"]
    d["hist"] = (macd - sig) / d["Close"]
    d["atr"] = atr(d)
    d["atr_pct"] = d["atr"] / d["Close"]
    mid = d["Close"].rolling(20).mean()
    sd = d["Close"].rolling(20).std()
    lo, hi = mid - 2 * sd, mid + 2 * sd
    d["bb_pos"] = (d["Close"] - lo) / (hi - lo).replace(0, np.nan)
    d["vol_ratio"] = d["Volume"] / d["Volume"].rolling(20).mean()
    d["volatility"] = d["Close"].pct_change().rolling(10).std()
    d["range_pct"] = (d["High"] - d["Low"]) / d["Close"]
    for n in [1, 3, 5, 10]:
        d[f"ret{n}"] = d["Close"].pct_change(n)
    d["ema8_21"] = d["ema8"] / d["ema21"] - 1
    d["ema21_55"] = d["ema21"] / d["ema55"] - 1
    d["ema55_200"] = d["ema55"] / d["ema200"] - 1
    d["market_ret5"] = (1 + d["market_ret1"]).rolling(5).apply(np.prod, raw=True) - 1
    d["relative5"] = d["ret5"] - d["market_ret5"]
    d["donchian20"] = d["High"].rolling(20).max().shift(1)
    d["donchian55"] = d["High"].rolling(55).max().shift(1)
    d["future_return"] = d["Close"].shift(-future) / d["Close"] - 1
    d["target"] = (d["future_return"] > target_pct).astype(int)
    return d.replace([np.inf, -np.inf], np.nan).dropna()


def signal_components(d: pd.DataFrame, raw_signal: pd.Series, fee: float = 0.0015):
    sig = pd.Series(raw_signal, index=d.index).reindex(d.index).fillna(False).astype(bool)
    pos = sig.shift(1, fill_value=False).astype(float)
    daily = d["Close"].pct_change().fillna(0.0)
    turns = pos.diff().abs().fillna(pos.abs())
    strat = pos * daily - turns * fee
    return sig, pos, daily, turns, strat


def timing_pvalue(d: pd.DataFrame, raw_signal: pd.Series, fee: float = 0.0015, permutations: int = 120, seed: int = 2026) -> float:
    if d.empty:
        return 1.0
    _, pos, daily, turns, strat = signal_components(d, raw_signal, fee)
    actual = float((1 + strat).prod() - 1)
    vals = daily.to_numpy(copy=True)
    rng = np.random.default_rng(seed)
    ge = 0
    for _ in range(permutations):
        perm = rng.permutation(vals)
        r = pos.to_numpy() * perm - turns.to_numpy() * fee
        sim = float(np.prod(1 + r) - 1)
        ge += sim >= actual
    return float((ge + 1) / (permutations + 1))


def perf_from_signal(d: pd.DataFrame, raw_signal: pd.Series, fee: float = 0.0015) -> Perf:
    if d.empty:
        return Perf(0.0, 0.0, 0, np.nan, np.nan, 0.0)
    sig, pos, daily, turns, strat = signal_components(d, raw_signal, fee)
    equity = (1 + strat).cumprod()
    total = float(equity.iloc[-1] - 1)
    mdd = float((equity / equity.cummax() - 1).min())
    sharpe = float(np.sqrt(252) * strat.mean() / strat.std()) if len(strat) > 5 and strat.std() > 0 else 0.0
    entries = pos.diff().fillna(pos) == 1
    exits = pos.diff().fillna(0) == -1
    trade_returns: List[float] = []
    start_idx: Optional[int] = None
    for i in range(len(d)):
        if bool(entries.iloc[i]) and start_idx is None:
            start_idx = i
        if start_idx is not None and (bool(exits.iloc[i]) or i == len(d) - 1):
            seg = strat.iloc[start_idx : i + 1]
            trade_returns.append(float((1 + seg).prod() - 1))
            start_idx = None
    trades = len(trade_returns)
    winrate = float(np.mean(np.array(trade_returns) > 0)) if trades else np.nan
    pf = np.nan
    if trades:
        pos_sum = sum(x for x in trade_returns if x > 0)
        neg_sum = abs(sum(x for x in trade_returns if x <= 0))
        if neg_sum > 0:
            pf = float(pos_sum / neg_sum)
    return Perf(total, mdd, trades, winrate, pf, sharpe)


def _mean_reversion_signal(d: pd.DataFrame, buy_bb: float, buy_rsi: float, exit_bb: float = 0.55, exit_rsi: float = 55) -> pd.Series:
    out: List[bool] = []
    active = False
    for _, row in d.iterrows():
        if not active and row["bb_pos"] <= buy_bb and row["rsi"] <= buy_rsi and row["Close"] > row["ema200"] * 0.85:
            active = True
        elif active and (row["bb_pos"] >= exit_bb or row["rsi"] >= exit_rsi or row["Close"] < row["ema200"] * 0.78):
            active = False
        out.append(active)
    return pd.Series(out, index=d.index)


def _breakout_signal(d: pd.DataFrame, lookback: int, vol_min: float) -> pd.Series:
    level = d["donchian20"] if lookback == 20 else d["donchian55"]
    out: List[bool] = []
    active = False
    for i, (_, row) in enumerate(d.iterrows()):
        lv = float(level.iloc[i]) if pd.notna(level.iloc[i]) else np.nan
        if not active and np.isfinite(lv) and row["Close"] > lv and row["vol_ratio"] >= vol_min and row["Close"] > row["ema55"]:
            active = True
        elif active and (row["Close"] < row["ema20"] or row["rsi"] < 45):
            active = False
        out.append(active)
    return pd.Series(out, index=d.index)


def build_rule_signal(d: pd.DataFrame, kind: str, params: Dict[str, float]) -> pd.Series:
    if kind == "추세":
        fast, slow = int(params["fast"]), int(params["slow"])
        sf = d[f"ema{fast}"] if f"ema{fast}" in d.columns else ema(d["Close"], fast)
        ss = d[f"ema{slow}"] if f"ema{slow}" in d.columns else ema(d["Close"], slow)
        return (d["Close"] > ss) & (sf > ss) & d["rsi"].between(48, params["rsi_max"]) & (d["vol_ratio"] >= params.get("vol_min", 0.65))
    if kind == "반전":
        return _mean_reversion_signal(d, params["bb"], params["rsi"])
    if kind == "돌파":
        return _breakout_signal(d, int(params["lookback"]), params["vol"])
    raise ValueError(f"Unknown rule strategy: {kind}")


def rule_param_grid() -> List[Tuple[str, Dict[str, float]]]:
    grid: List[Tuple[str, Dict[str, float]]] = []
    for fast, slow, ceil, vol in [(8, 55, 76, 0.65), (8, 55, 82, 0.8), (21, 100, 76, 0.65), (21, 200, 74, 0.7)]:
        grid.append(("추세", {"fast": fast, "slow": slow, "rsi_max": ceil, "vol_min": vol}))
    for bb, rr in [(0.10, 35), (0.18, 38), (0.25, 40)]:
        grid.append(("반전", {"bb": bb, "rsi": rr}))
    for lb, vol in [(20, 0.9), (20, 1.15), (55, 1.0)]:
        grid.append(("돌파", {"lookback": lb, "vol": vol}))
    return grid


def _segment_perf(pretest: pd.DataFrame, sig: pd.Series, fee: float, segments: int = 3) -> List[Perf]:
    n = len(pretest)
    start = int(n * 0.40)
    edges = np.linspace(start, n, segments + 1, dtype=int)
    perfs: List[Perf] = []
    for i in range(segments):
        seg = pretest.iloc[edges[i] : edges[i + 1]]
        if len(seg) < 40:
            continue
        perfs.append(perf_from_signal(seg, sig.reindex(seg.index), fee))
    return perfs


def _stability_score(perfs: Iterable[Perf]) -> Tuple[float, float, float, int]:
    ps = list(perfs)
    if not ps:
        return -999.0, -1.0, 0.0, 0
    returns = np.array([p.ret for p in ps], dtype=float)
    positive_ratio = float(np.mean(returns > 0))
    median_return = float(np.median(returns))
    trades = int(sum(p.trades for p in ps))
    med_sharpe = float(np.median([p.sharpe for p in ps]))
    med_mdd = float(np.median([p.mdd for p in ps]))
    score = median_return * 3.0 + positive_ratio * 0.35 + med_sharpe * 0.08 + med_mdd * 0.5 + min(trades, 30) * 0.003
    if positive_ratio < 2 / 3 or trades < 4:
        score -= 0.5
    return score, median_return, positive_ratio, trades


def select_rule(pretest: pd.DataFrame, full: pd.DataFrame, fee: float) -> Optional[StrategyChoice]:
    ranked: List[Tuple[float, StrategyChoice]] = []
    for kind, params in rule_param_grid():
        sig = build_rule_signal(full, kind, params)
        perfs = _segment_perf(pretest, sig, fee)
        score, med_ret, pos_ratio, trades = _stability_score(perfs)
        ranked.append((score, StrategyChoice(kind, params, score, med_ret, pos_ratio, trades)))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[0][1] if ranked and ranked[0][0] > -0.25 else None


def ai_models(fast_mode: bool = True):
    hgb_iter = 80 if fast_mode else 140
    return {
        "LR": Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(max_iter=800, class_weight="balanced", C=0.35))]),
        "HGB": HistGradientBoostingClassifier(max_iter=hgb_iter, max_leaf_nodes=12, learning_rate=0.05, l2_regularization=1.5, random_state=42),
    }


def ai_oof(pretest: pd.DataFrame, future: int, fast_mode: bool = True) -> Tuple[pd.Series, float]:
    splits = 3 if fast_mode else 4
    tss = TimeSeriesSplit(n_splits=splits, gap=max(1, future))
    oof = pd.Series(np.nan, index=pretest.index, dtype=float)
    aucs: List[float] = []
    for tr_idx, va_idx in tss.split(pretest):
        tr, va = pretest.iloc[tr_idx], pretest.iloc[va_idx]
        if tr["target"].nunique() < 2 or va["target"].nunique() < 2:
            continue
        fold_preds: List[np.ndarray] = []
        for model in ai_models(fast_mode).values():
            model.fit(tr[FEATURES], tr["target"])
            fold_preds.append(model.predict_proba(va[FEATURES])[:, 1])
        p = np.mean(np.vstack(fold_preds), axis=0)
        oof.loc[va.index] = p
        aucs.append(float(roc_auc_score(va["target"], p)))
    return oof, float(np.mean(aucs)) if aucs else np.nan


def fit_ai_predict(pretest: pd.DataFrame, test: pd.DataFrame, fast_mode: bool = True) -> np.ndarray:
    preds: List[np.ndarray] = []
    for model in ai_models(fast_mode).values():
        model.fit(pretest[FEATURES], pretest["target"])
        preds.append(model.predict_proba(test[FEATURES])[:, 1])
    return np.mean(np.vstack(preds), axis=0)


def select_ai(pretest: pd.DataFrame, future: int, fee: float, fast_mode: bool) -> Optional[StrategyChoice]:
    oof, auc = ai_oof(pretest, future, fast_mode)
    if not np.isfinite(auc) or auc < 0.50:
        return None
    ranked: List[Tuple[float, StrategyChoice]] = []
    for th in [0.52, 0.56, 0.60, 0.64]:
        sig = (oof >= th) & (pretest["Close"] > pretest["ema55"]) & pretest["rsi"].between(45, 78)
        perfs = _segment_perf(pretest, sig, fee)
        score, med_ret, pos_ratio, trades = _stability_score(perfs)
        choice = StrategyChoice("AI", {"threshold": th}, score, med_ret, pos_ratio, trades, auc)
        ranked.append((score, choice))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[0][1] if ranked and ranked[0][0] > -0.25 else None


def analyze_frame(name: str, ticker: str, data: pd.DataFrame, future: int = 5, fee: float = 0.0015, fast_mode: bool = True) -> Dict[str, object]:
    if len(data) < 850:
        raise ValueError("데이터 부족")
    split = int(len(data) * 0.75)
    pretest = data.iloc[:split].copy()
    test = data.iloc[split:].copy()
    if len(test) < 150:
        raise ValueError("최종 검증 구간 부족")

    rule_choice = select_rule(pretest, data, fee)
    ai_choice = select_ai(pretest, future, fee, fast_mode) if pretest["target"].nunique() > 1 else None
    choices = [c for c in [rule_choice, ai_choice] if c is not None]
    if not choices:
        raise ValueError("안정적인 후보 전략 없음")
    choice = max(choices, key=lambda c: c.validation_score)

    test_auc = np.nan
    if choice.kind == "AI":
        p = fit_ai_predict(pretest, test, fast_mode)
        test_auc = float(roc_auc_score(test["target"], p)) if test["target"].nunique() > 1 else np.nan
        test_sig = (pd.Series(p, index=test.index) >= choice.params["threshold"]) & (test["Close"] > test["ema55"]) & test["rsi"].between(45, 78)
    else:
        full_sig = build_rule_signal(data, choice.kind, choice.params)
        test_sig = full_sig.reindex(test.index)

    test_perf = perf_from_signal(test, test_sig, fee)
    ntest = len(test)
    edges = np.linspace(0, ntest, 4, dtype=int)
    test_sub = [perf_from_signal(test.iloc[edges[i]:edges[i+1]], test_sig.reindex(test.iloc[edges[i]:edges[i+1]].index), fee) for i in range(3)]
    test_positive_ratio = float(np.mean([p.ret > 0 for p in test_sub]))
    test_median_return = float(np.median([p.ret for p in test_sub]))
    timing_p = timing_pvalue(test, test_sig, fee, permutations=80 if fast_mode else 200)
    recent_n = min(63, len(test))
    recent = test.iloc[-recent_n:]
    recent_perf = perf_from_signal(recent, test_sig.reindex(recent.index), fee)
    buyhold = float(test["Close"].iloc[-1] / test["Close"].iloc[0] - 1)

    reasons: List[str] = []
    if choice.validation_positive_ratio < 2 / 3:
        reasons.append("사전안정성")
    if choice.validation_median_return <= 0:
        reasons.append("사전수익")
    if test_perf.ret <= 0:
        reasons.append("TEST수익")
    min_test_trades = max(5, int(round((len(test) / 252.0) * 4)))
    if test_perf.trades < min_test_trades:
        reasons.append("TEST거래수")
    if test_positive_ratio < 2 / 3 or test_median_return <= 0:
        reasons.append("TEST안정성")
    if not np.isfinite(test_perf.pf) or test_perf.pf < 1.15:
        reasons.append("PF")
    if test_perf.mdd < -0.18:
        reasons.append("MDD")
    if test_perf.sharpe < 0.20:
        reasons.append("샤프")
    if recent_perf.ret < -0.04:
        reasons.append("최근63일")
    if choice.kind == "AI":
        if not np.isfinite(choice.ai_oof_auc) or choice.ai_oof_auc < 0.53:
            reasons.append("AI OOF")
        if not np.isfinite(test_auc) or test_auc < 0.52:
            reasons.append("AI TEST")

    core_pass = len(reasons) == 0
    if core_pass and timing_p <= 0.15:
        grade = "A"
    elif core_pass and timing_p <= 0.35:
        grade = "B"
    elif core_pass:
        grade = "관찰"
    else:
        grade = "탈락"
    passed = grade == "A"
    score = (
        choice.validation_median_return * 20
        + choice.validation_positive_ratio * 2
        + test_perf.ret * 35
        + min(test_perf.pf if np.isfinite(test_perf.pf) else 0, 3) * 1.5
        + test_perf.sharpe * 2.5
        + test_perf.mdd * 8
        + recent_perf.ret * 8
        + min(test_perf.trades, 20) * 0.05
    )
    return {
        "통과": "✅" if passed else "❌",
        "등급": grade,
        "종목": name,
        "코드": ticker,
        "선택전략": choice.kind,
        "사전중앙수익": choice.validation_median_return,
        "사전양수비율": choice.validation_positive_ratio,
        "TEST수익": test_perf.ret,
        "TEST구간양수비율": test_positive_ratio,
        "TEST구간중앙수익": test_median_return,
        "타이밍p": timing_p,
        "최근63일": recent_perf.ret,
        "매수보유": buyhold,
        "MDD": test_perf.mdd,
        "TEST거래수": test_perf.trades,
        "승률": test_perf.winrate,
        "PF": test_perf.pf,
        "샤프": test_perf.sharpe,
        "AI OOF AUC": choice.ai_oof_auc if choice.kind == "AI" else np.nan,
        "AI TEST AUC": test_auc if choice.kind == "AI" else np.nan,
        "탈락사유": "-" if passed else ", ".join(reasons),
        "점수": score,
    }


def synthetic_ohlcv(seed: int = 42, n: int = 1400, regime: str = "random") -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    if regime == "trend":
        r = rng.normal(0.00065, 0.010, n)
        r += 0.0007 * (np.sin(np.arange(n) / 55) > -0.25)
    elif regime == "mean_revert":
        x = np.zeros(n)
        for i in range(1, n):
            x[i] = 0.94 * x[i - 1] + rng.normal(0, 0.012)
        close = 100 * np.exp(x + np.linspace(0, 0.15, n))
        r = np.r_[0, np.diff(np.log(close))]
    else:
        r = rng.normal(0.0001, 0.012, n)
    close = 100 * np.exp(np.cumsum(r))
    open_ = close * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.004, n)))
    volume = rng.integers(200_000, 2_000_000, n)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=idx)


def run_self_tests() -> Dict[str, bool]:
    out: Dict[str, bool] = {}
    idx = pd.date_range("2024-01-01", periods=100, freq="B")
    close = np.linspace(100, 140, len(idx))
    d = pd.DataFrame({"Close": close}, index=idx)
    p0 = perf_from_signal(d, pd.Series(False, index=idx))
    out["no_signal_zero_return"] = abs(p0.ret) < 1e-12 and p0.trades == 0
    p1 = perf_from_signal(d, pd.Series(True, index=idx), fee=0.0)
    out["next_bar_positive_trend"] = p1.ret > 0 and p1.mdd <= 1e-12

    raw = synthetic_ohlcv(seed=1, n=800, regime="trend")
    market = synthetic_ohlcv(seed=2, n=800, regime="random")
    f1 = make_features(raw, market, future=5)
    cutoff = raw.index[600]
    raw2 = raw.copy()
    raw2.loc[raw2.index > cutoff, ["Open", "High", "Low", "Close"]] *= 4.0
    f2 = make_features(raw2, market, future=5)
    common = f1.index.intersection(f2.index)
    common = common[common <= cutoff]
    common = common[:-6] if len(common) > 6 else common
    cols = FEATURES + ["ema20", "ema55", "donchian20", "donchian55"]
    out["causal_features"] = bool(np.allclose(f1.loc[common, cols], f2.loc[common, cols], equal_nan=True, rtol=1e-10, atol=1e-10))

    raw3 = synthetic_ohlcv(seed=7, n=1400, regime="random")
    market3 = synthetic_ohlcv(seed=8, n=1400, regime="random")
    data3 = make_features(raw3, market3, future=5)
    try:
        result = analyze_frame("SYN", "SYN", data3, future=5, fast_mode=True)
        out["full_pipeline_smoke"] = result["통과"] in {"✅", "❌"}
    except ValueError as e:
        out["full_pipeline_smoke"] = "후보" in str(e) or "안정" in str(e)
    return out
