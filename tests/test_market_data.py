import pandas as pd
import pytest

from market_data import MAX_SINGLE_REPAIR_EXCESS, apply_adj_close_factor, normalize_ohlcv


def good_frame(n=20):
    idx = pd.date_range("2026-01-01", periods=n, freq="B")
    base = pd.Series(range(n), index=idx, dtype=float)
    return pd.DataFrame({
        "Open": 100 + base,
        "High": 102 + base,
        "Low": 99 + base,
        "Close": 101 + base,
        "Volume": 1000 + base * 10,
    }, index=idx)


def test_valid_ohlcv_passes_without_repairs():
    out = normalize_ohlcv(good_frame(), "TEST")
    assert list(out.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert len(out) == 20
    assert out.attrs["ohlcv_repaired_bars"] == 0


def test_duplicate_dates_are_rejected():
    d = good_frame()
    d = pd.concat([d, d.iloc[[0]]])
    with pytest.raises(ValueError, match="duplicate market dates"):
        normalize_ohlcv(d, "TEST")


def test_one_adj_close_factor_preserves_candle_geometry_and_volume():
    d = good_frame(3)
    d["Adj Close"] = d["Close"] * pd.Series([0.5, 0.8, 1.0], index=d.index)
    adjusted = apply_adj_close_factor(d, "TEST")
    assert adjusted.iloc[0]["Open"] == pytest.approx(50.0)
    assert adjusted.iloc[0]["High"] == pytest.approx(51.0)
    assert adjusted.iloc[0]["Low"] == pytest.approx(49.5)
    assert adjusted.iloc[0]["Close"] == pytest.approx(50.5)
    assert adjusted.iloc[0]["Volume"] == 1000


def test_isolated_high_low_defect_is_minimally_repaired():
    d = good_frame()
    date = d.index[5]
    d.loc[date, "High"] = d.loc[date, "Close"] * 0.98
    d.loc[date, "Low"] = d.loc[date, "Open"] * 1.01
    original_open = d.loc[date, "Open"]
    original_close = d.loc[date, "Close"]
    out = normalize_ohlcv(d, "TEST")
    assert out.loc[date, "Open"] == original_open
    assert out.loc[date, "Close"] == original_close
    assert out.loc[date, "High"] >= max(original_open, original_close)
    assert out.loc[date, "Low"] <= min(original_open, original_close)
    assert out.attrs["ohlcv_repaired_bars"] == 1


def test_single_extreme_range_defect_is_quarantined():
    d = good_frame()
    date = d.index[4]
    d.loc[date, "High"] = d.loc[date, "Close"] * (1 - MAX_SINGLE_REPAIR_EXCESS - 0.03)
    with pytest.raises(ValueError, match="repair too large"):
        normalize_ohlcv(d, "TEST")


def test_too_many_range_defects_are_quarantined():
    d = good_frame(100)
    for date in d.index[:5]:
        d.loc[date, "High"] = d.loc[date, "Close"] * 0.99
    with pytest.raises(ValueError, match="too many OHLC range repairs"):
        normalize_ohlcv(d, "TEST")


def test_non_positive_price_is_rejected():
    d = good_frame()
    d.loc[d.index[0], "Close"] = 0
    with pytest.raises(ValueError, match="non-positive price"):
        normalize_ohlcv(d, "TEST")
