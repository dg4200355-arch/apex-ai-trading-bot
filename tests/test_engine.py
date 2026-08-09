import numpy as np
import pandas as pd

from engine import (
    analyze_frame,
    build_rule_signal,
    make_features,
    perf_from_signal,
    run_self_tests,
    synthetic_ohlcv,
)


def test_self_tests_all_pass():
    result = run_self_tests()
    assert result and all(result.values()), result


def test_future_perturbation_does_not_change_past_rule_signal():
    raw = synthetic_ohlcv(seed=11, n=900, regime="trend")
    market = synthetic_ohlcv(seed=12, n=900, regime="random")
    d1 = make_features(raw, market, future=5)
    cutoff = raw.index[700]
    raw2 = raw.copy()
    raw2.loc[raw2.index > cutoff, ["Open", "High", "Low", "Close"]] *= 0.25
    d2 = make_features(raw2, market, future=5)
    s1 = build_rule_signal(d1, "추세", {"fast": 8, "slow": 55, "rsi_max": 76, "vol_min": 0.65})
    s2 = build_rule_signal(d2, "추세", {"fast": 8, "slow": 55, "rsi_max": 76, "vol_min": 0.65})
    common = s1.index.intersection(s2.index)
    common = common[common <= cutoff]
    common = common[:-6]
    assert (s1.loc[common].values == s2.loc[common].values).all()


def test_costs_reduce_return():
    idx = pd.date_range("2024-01-01", periods=100, freq="B")
    d = pd.DataFrame({"Close": np.linspace(100, 150, 100)}, index=idx)
    sig = pd.Series(True, index=idx)
    free = perf_from_signal(d, sig, fee=0)
    costly = perf_from_signal(d, sig, fee=0.002)
    assert costly.ret < free.ret


def test_random_pipeline_is_finite_or_strictly_rejected():
    raw = synthetic_ohlcv(seed=21, n=1500, regime="random")
    market = synthetic_ohlcv(seed=22, n=1500, regime="random")
    data = make_features(raw, market, future=5)
    try:
        result = analyze_frame("RANDOM", "RND", data, future=5, fast_mode=True)
        assert np.isfinite(result["TEST수익"])
        assert result["통과"] in {"✅", "❌"}
    except ValueError as e:
        assert "후보" in str(e) or "검증" in str(e) or "데이터" in str(e)
