"""Network smoke test for CI. A rejected strategy is a valid outcome; data/engine crashes are not."""
import sys
import yfinance as yf
import pandas as pd

from engine import make_features, analyze_frame


def dl(ticker):
    d = yf.download(ticker, period="5y", interval="1d", auto_adjust=True, progress=False, threads=False)
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    return d[["Open","High","Low","Close","Volume"]].dropna()


def main():
    cases = [("Apple", "AAPL", "SPY"), ("삼성전자", "005930.KS", "^KS11")]
    usable = 0
    for name, ticker, bench in cases:
        try:
            raw, market = dl(ticker), dl(bench)
            if len(raw) < 900 or len(market) < 900:
                raise RuntimeError("insufficient market history")
            data = make_features(raw, market, future=5, target_pct=.01)
            try:
                result = analyze_frame(name, ticker, data, future=5, fee=.0015, fast_mode=True)
                print(ticker, result["등급"], result["선택전략"], result["TEST수익"], result["탈락사유"])
            except ValueError as e:
                print(ticker, "strict-rejection", str(e))
            usable += 1
        except Exception as e:
            print(ticker, "DATA_ERROR", repr(e), file=sys.stderr)
    if usable == 0:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
