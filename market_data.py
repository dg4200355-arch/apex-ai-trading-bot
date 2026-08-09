"""Central market-data download and OHLCV integrity checks for APEX.

Research/backtests use dividend/split-adjusted OHLC so indicators and historical
returns are comparable. Shadow-broker executions use immutable raw trade prices;
past fills must never be rewritten by a later dividend adjustment.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

REQUIRED = ["Open", "High", "Low", "Close", "Volume"]
MAX_REPAIR_FRACTION = 0.01
MIN_ALLOWED_REPAIR_BARS = 3
MAX_SINGLE_REPAIR_EXCESS = 0.05


def _flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    d = frame.copy()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    return d


def apply_adj_close_factor(frame: pd.DataFrame, ticker: str = "?") -> pd.DataFrame:
    """Adjust O/H/L/C with one common Adj Close / raw Close factor."""
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
    good = np.isfinite(factor) & (factor > 0)
    d = d.loc[good].copy()
    factor = factor.loc[good]
    if d.empty:
        raise ValueError(f"no valid adjustment factors: {ticker}")
    for col in ["Open", "High", "Low", "Close"]:
        d[col] = d[col] * factor
    return d[REQUIRED].copy()


def _repair_isolated_range_defects(d: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Conservatively repair isolated High/Low defects without touching Open/Close."""
    out = d.copy()
    true_high = out[["Open", "High", "Close"]].max(axis=1)
    true_low = out[["Open", "Low", "Close"]].min(axis=1)
    repair_high = true_high > out["High"]
    repair_low = true_low < out["Low"]
    crossed = out["High"] < out["Low"]
    repair_mask = repair_high | repair_low | crossed
    repair_count = int(repair_mask.sum())

    high_excess = ((true_high - out["High"]) / out[["High", "Open", "Close"]].abs().max(axis=1).replace(0, np.nan)).clip(lower=0)
    low_excess = ((out["Low"] - true_low) / out[["Low", "Open", "Close"]].abs().max(axis=1).replace(0, np.nan)).clip(lower=0)
    severity = pd.concat([high_excess, low_excess], axis=1).max(axis=1).fillna(0.0)
    worst = float(severity.loc[repair_mask].max()) if repair_count else 0.0
    worst_date = None
    if repair_count:
        worst_date = pd.Timestamp(severity.loc[repair_mask].idxmax()).date().isoformat()

    allowed = max(MIN_ALLOWED_REPAIR_BARS, int(np.ceil(len(out) * MAX_REPAIR_FRACTION)))
    if repair_count > allowed:
        raise ValueError(
            f"too many OHLC range repairs: {ticker} repairs={repair_count} allowed={allowed} rows={len(out)}"
        )
    if worst > MAX_SINGLE_REPAIR_EXCESS:
        raise ValueError(
            f"OHLC range repair too large: {ticker} date={worst_date} excess={worst:.4%} max={MAX_SINGLE_REPAIR_EXCESS:.2%}"
        )

    if repair_count:
        out.loc[repair_mask, "High"] = true_high.loc[repair_mask]
        out.loc[repair_mask, "Low"] = true_low.loc[repair_mask]
    out.attrs["ohlcv_repaired_bars"] = repair_count
    out.attrs["ohlcv_max_repair_pct"] = worst
    return out


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

    d = _repair_isolated_range_defects(d, ticker)
    if (d["High"] < d[["Open", "Close"]].max(axis=1)).any():
        raise ValueError(f"high invariant remains after repair: {ticker}")
    if (d["Low"] > d[["Open", "Close"]].min(axis=1)).any():
        raise ValueError(f"low invariant remains after repair: {ticker}")
    if (d["High"] < d["Low"]).any():
        raise ValueError(f"high-low invariant remains after repair: {ticker}")
    if not d.index.is_monotonic_increasing:
        raise ValueError(f"non-monotonic market dates: {ticker}")
    return d


def _download_yahoo(
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
    return yf.download(**kwargs)


def download_ohlcv(
    ticker: str,
    *,
    period: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """Adjusted OHLCV for research, model features, and historical validation."""
    raw = _download_yahoo(ticker, period=period, start=start, end=end)
    adjusted = apply_adj_close_factor(raw, ticker)
    out = normalize_ohlcv(adjusted, ticker)
    out.attrs["price_basis"] = "ADJUSTED_RESEARCH"
    return out


def download_trade_ohlcv(
    ticker: str,
    *,
    period: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """Raw unadjusted OHLCV for paper fills and account valuation.

    Historical raw opens/closes are stable execution prices. This prevents a later
    dividend adjustment from rewriting an already-recorded paper fill.
    """
    raw = _download_yahoo(ticker, period=period, start=start, end=end)
    d = _flatten_columns(raw)
    out = normalize_ohlcv(d[REQUIRED].copy(), ticker)
    out.attrs["price_basis"] = "RAW_EXECUTION"
    return out
