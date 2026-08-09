import pandas as pd
import pytest

from market_data import RANGE_REL_TOL, apply_adj_close_factor, normalize_ohlcv


def good_frame():
    idx = pd.date_range("2026-01-01", periods=3, freq="B")
    return pd.DataFrame({
        "Open": [100, 101, 102],
        "High": [102, 103, 104],
        "Low": [99, 100, 101],
        "Close": [101, 102, 103],
        "Volume": [1000, 1200, 900],
    }, index=idx)


def test_valid_ohlcv_passes():
    out = normalize_ohlcv(good_frame(), "TEST")
    assert list(out.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert len(out) == 3


def test_duplicate_dates_are_rejected():
    d = good_frame()
    d = pd.concat([d, d.iloc[[0]]])
    with pytest.raises(ValueError, match="duplicate market dates"):
        normalize_ohlcv(d, "TEST")


def test_one_adj_close_factor_preserves_candle_geometry_and_volume():
    d = good_frame()
    d["Adj Close"] = d["Close"] * pd.Series([0.5, 0.8, 1.0], index=d.index)
    adjusted = apply_adj_close_factor(d, "TEST")
    assert adjusted.loc[d.index[0], "Open"] == pytest.approx(50.0)
    assert adjusted.loc[d.index[0], "High"] == pytest.approx(51.0)
    assert adjusted.loc[d.index[0], "Low"] == pytest.approx(49.5)
    assert adjusted.loc[d.index[0], "Close"] == pytest.approx(50.5)
    assert adjusted.loc[d.index[0], "Volume"] == 1000
    out = normalize_ohlcv(adjusted, "TEST")
    assert len(out) == 3


def test_small_post_adjustment_rounding_mismatch_is_tolerated():
    d = good_frame()
    d.loc[d.index[1], "High"] = 101.97
    d.loc[d.index[1], "Close"] = 102.0
    assert (102.0 / 101.97 - 1) < RANGE_REL_TOL
    out = normalize_ohlcv(d, "TEST")
    assert len(out) == 3


def test_material_high_invariant_is_rejected():
    d = good_frame()
    d.loc[d.index[1], "High"] = 99
    with pytest.raises(ValueError, match="high-price invariant|high-low invariant"):
        normalize_ohlcv(d, "TEST")


def test_high_below_low_is_rejected():
    d = good_frame()
    d.loc[d.index[1], "High"] = 95
    with pytest.raises(ValueError, match="high-low invariant"):
        normalize_ohlcv(d, "TEST")


def test_non_positive_price_is_rejected():
    d = good_frame()
    d.loc[d.index[0], "Close"] = 0
    with pytest.raises(ValueError, match="non-positive price"):
        normalize_ohlcv(d, "TEST")
