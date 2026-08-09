import pandas as pd
import pytest

from market_data import normalize_ohlcv


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


def test_high_invariant_is_rejected():
    d = good_frame()
    d.loc[d.index[1], "High"] = 99
    with pytest.raises(ValueError, match="high-price invariant"):
        normalize_ohlcv(d, "TEST")


def test_non_positive_price_is_rejected():
    d = good_frame()
    d.loc[d.index[0], "Close"] = 0
    with pytest.raises(ValueError, match="non-positive price"):
        normalize_ohlcv(d, "TEST")
