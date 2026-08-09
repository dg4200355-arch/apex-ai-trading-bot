"""Central market-data download and OHLCV integrity checks for APEX."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

REQUIRED = ["Open", "High", "Low", "Close", "Volume"]
# After one-factor manual adjustment, only tiny floating/rounding drift is allowed.
RANGE_REL_TOL = 0.0005


def _flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    d = frame.copy()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    return d


def _worst_positive(series: pd.Series):
    clean = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        return None, 0.0
    idx = clean.idxmax()
    return idx, float(clean.loc[idx])


def apply_adj_close_factor(frame: pd.DataFrame, ticker: str = "?") -> pd.DataFrame:
    """Adjust O/H/L/C with one common Adj Close / raw Close factor.

    yfinance auto_adjust=True can occasionally expose historical Korean OHLC bars
    whose Open/High/Low/Close no longer share exactly the same adjustment basis.
    Pulling raw OHLC plus Adj Close and applying one factor ourselves preserves the
    candle geometry while still accounting for splits/dividends.
    """
    d = _flatten_columns(frame)
    missing = [c for c in REQUIRED if c not in d.columns]
    if missing:
        raise ValueError(f"missing OHLCV columns {missing}: {ticker}")

    for col in REQUIRED + (["Adj Close"] if "Adj Close" in d.columns else []):
        d[col] = pd.to_numeric(d[col], errors="coerce")

    if "Adj Close" not in d.columns:
        return d[REQUIRED].copy()

    raw_close = d["Close"].replace(0, np.nan)
    factor = d["Adj Close"] / raw_close
    bad_factor = (~np.isfinite(factor)) | (factor <= 0)
    if bad_factor.any():
        d = d.loc[~bad_factor].copy()
        factor = factor.loc[~bad_factor]
    if d.empty:
        raise ValueError(f"no valid adjustment factors: {ticker}")

    for col in ["Open", "High", "Low", "Close"]:
        d[col] = d[col] * factor
    return d[REQUIRED].copy()


def normalize_ohlcv(frame: pd.DataFrame, ticker: str = "?") -> pd.DataFrame:
    if frame is None or frame.empty:
        raise ValueError(f"empty OHLCV: {ticker}")
    d = _flatten_columns(frame)
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

    crossed = d["High"] < d["Low"]
    if crossed.any():
        date = pd.Timestamp(crossed[crossed].index[0]).date().isoformat()
        raise ValueError(f"high-low invariant failed: {ticker} date={date}")

    oc_high = d[["Open", "Close"]].max(axis=1)
    high_excess = (oc_high - d["High"]) / d["High"]
    high_date, high_worst = _worst_positive(high_excess)
    if high_worst > RANGE_REL_TOL:
        date = pd.Timestamp(high_date).date().isoformat()
        raise ValueError(
            f"high-price invariant failed: {ticker} date={date} excess={high_worst:.4%} tol={RANGE_REL_TOL:.2%}"
        )

    oc_low = d[["Open", "Close"]].min(axis=1)
    low_excess = (d["Low"] - oc_low) / d["Low"]
    low_date, low_worst = _worst_positive(low_excess)
    if low_worst > RANGE_REL_TOL:
        date = pd.Timestamp(low_date).date().isoformat()
        raise ValueError(
            f"low-price invariant failed: {ticker} date={date} excess={low_worst:.4%} tol={RANGE_REL_TOL:.2%}"
        )

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
        "auto_adjust": False,
        "actions": False,
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
    adjusted = apply_adj_close_factor(raw, ticker)
    return normalize_ohlcv(adjusted, ticker)
