# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-10-12T00:41:09+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 5
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 6

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=284.78%, PF=3.58, timing_p=0.333, q80=1.000, repairs=0, embargo=5, data_end=2026-10-09
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=174.34%, PF=8.49, timing_p=0.259, q80=0.988, repairs=3, embargo=5, data_end=2026-10-12
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=110.78%, PF=2.54, timing_p=0.259, q80=0.988, repairs=0, embargo=5, data_end=2026-10-09
- 탈락 한화오션 (042660.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=72.66%, PF=nan, timing_p=0.012, q80=0.988, repairs=3, embargo=5, data_end=2026-10-12
- 탈락 삼성물산 (028260.KS): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=54.74%, PF=1.69, timing_p=0.346, q80=1.000, repairs=1, embargo=5, data_end=2026-10-12
- 탈락 Alphabet (GOOGL): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=22.75%, PF=41.89, timing_p=0.111, q80=0.988, repairs=0, embargo=5, data_end=2026-10-09
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=0.988, repairs=0, embargo=5, data_end=2026-10-09
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=15.54%, PF=1.41, timing_p=0.259, q80=0.988, repairs=3, embargo=5, data_end=2026-10-12
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=17.09%, PF=3.40, timing_p=0.160, q80=0.988, repairs=2, embargo=5, data_end=2026-10-12
- 관찰 Caterpillar (CAT): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=18.28%, PF=2.04, timing_p=0.506, q80=1.000, repairs=0, embargo=5, data_end=2026-10-09
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.53%, PF=4.90, timing_p=0.148, q80=0.988, repairs=0, embargo=5, data_end=2026-10-09
- B Chevron (CVX): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.64%, PF=16.03, timing_p=0.136, q80=0.988, repairs=0, embargo=5, data_end=2026-10-09
- 탈락 ExxonMobil (XOM): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=15.39%, PF=nan, timing_p=0.222, q80=0.988, repairs=0, embargo=5, data_end=2026-10-09
- 탈락 Berkshire (BRK-B): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=17.85%, PF=nan, timing_p=0.025, q80=0.988, repairs=0, embargo=5, data_end=2026-10-09
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=6.56%, PF=3.05, timing_p=0.185, q80=0.988, repairs=0, embargo=5, data_end=2026-10-09
