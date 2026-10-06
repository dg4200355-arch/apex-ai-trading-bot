# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-10-06T01:49:53+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 6
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 4

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=277.30%, PF=3.55, timing_p=0.346, q80=1.000, repairs=0, embargo=5, data_end=2026-10-05
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=174.34%, PF=8.49, timing_p=0.247, q80=1.000, repairs=3, embargo=5, data_end=2026-10-06
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=117.96%, PF=2.59, timing_p=0.259, q80=1.000, repairs=0, embargo=5, data_end=2026-10-05
- 탈락 한화오션 (042660.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=72.66%, PF=nan, timing_p=0.012, q80=0.988, repairs=3, embargo=5, data_end=2026-10-06
- 탈락 삼성물산 (028260.KS): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=54.90%, PF=1.69, timing_p=0.259, q80=1.000, repairs=1, embargo=5, data_end=2026-10-06
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=24.04%, PF=15.74, timing_p=0.049, q80=1.000, repairs=2, embargo=5, data_end=2026-10-06
- 탈락 Alphabet (GOOGL): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=22.75%, PF=41.89, timing_p=0.111, q80=1.000, repairs=0, embargo=5, data_end=2026-10-05
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=22.39%, PF=2.47, timing_p=0.432, q80=1.000, repairs=0, embargo=5, data_end=2026-10-05
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=15.48%, PF=1.40, timing_p=0.272, q80=1.000, repairs=3, embargo=5, data_end=2026-10-06
- B Berkshire (BRK-B): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=12.73%, PF=833.68, timing_p=0.062, q80=1.000, repairs=0, embargo=5, data_end=2026-10-05
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.53%, PF=4.90, timing_p=0.148, q80=1.000, repairs=0, embargo=5, data_end=2026-10-05
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=16.15%, PF=3.76, timing_p=0.247, q80=1.000, repairs=1, embargo=5, data_end=2026-10-06
- B Chevron (CVX): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.64%, PF=16.03, timing_p=0.160, q80=1.000, repairs=0, embargo=5, data_end=2026-10-05
- 탈락 AbbVie (ABBV): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=13.34%, PF=5.91, timing_p=0.370, q80=1.000, repairs=0, embargo=5, data_end=2026-10-05
- 탈락 ExxonMobil (XOM): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=15.39%, PF=nan, timing_p=0.235, q80=1.000, repairs=0, embargo=5, data_end=2026-10-05
