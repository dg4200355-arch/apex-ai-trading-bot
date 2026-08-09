"""Central market-data download and OHLCV integrity checks for APEX."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

REQUIRED = ["Open", "High", "Low", "Close", "Volume"]
# yfinance auto-adjusted OHLC can contain small range mismatches from vendor
# adjustment/rounding, especially on some Korean listings. 0.5% is tolerated;
# larger inconsistencies are still rejected as corrupted bars.
RANGE_REL_TOL = 0.005


def normalize_ohlcv(frame: pd.DataFrame, ticker: str = "?") -> pd.DataFrame:
    if frame is None or frame.empty:
        raise ValueError(f"empty OHLCV: {ticker}")
    d = frame.copy()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    missing = [c for c in REQUIRED if c not in d.columns]
    if missing:
        raise ValueError(f"missing OHLCV columns {missing}: {ticker}")
    d = d[REQUIRED].copy()
    d.index = pd.to_datetime(d.index)
    if getattr(d.index, "tz", None) is not None:
        d.index = d.index.tz_localize(None)
    d = d.sort_index()
    if d.index.has_duplicates:
        raise ValueError(f"duplicate market dates: {ticker}")
    for col in REQUIRED:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    d = d.replace([np.inf, -np.inf], np.nan).dropna()
    if len(d) < 2:
        raise ValueError(f"insufficient clean OHLCV: {ticker}")

    prices = d[["Open", "High", "Low", "Close"]]
    if (prices <= 0).any().any():
        raise ValueError(f"non-positive price: {ticker}")
    if (d["Volume"] < 0).any():
        raise ValueError(f"negative volume: {ticker}")

    # High must never be materially below Low.
    if (d["High"] < d["Low"] * (1 - RANGE_REL_TOL)).any():
        raise ValueError(f"high-low invariant failed: {ticker}")

    # Open/Close may differ from adjusted High/Low by tiny vendor-rounding amounts.
    upper = d["High"] * (1 + RANGE_REL_TOL)
    lower = d["Low"] * (1 - RANGE_REL_TOL)
    if ((d["Open"] > upper) | (d["Close"] > upper)).any():
        raise ValueError(f"high-price invariant failed: {ticker}")
    if ((d["Open"] < lower) | (d["Close"] < lower)).any():
        raise ValueError(f"low-price invariant failed: {ticker}")

    if not d.index.is_monotonic_increasing:
        raise ValueError(f"non-monotonic market dates: {ticker}")
    return d


def download_ohlcv(
    ticker: str,
    *,
    period: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    kwargs = {
        "tickers": ticker,
        "interval": "1d",
        "auto_adjust": True,
        "progress": False,
        "threads": False,
    }
    if period is not None:
        kwargs["period"] = period
    if start is not None:
        kwargs["start"] = start
    if end is not None:
        kwargs["end"] = end
    raw = yf.download(**kwargs)
    return normalize_ohlcv(raw, ticker)
