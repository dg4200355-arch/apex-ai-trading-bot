# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-09-30T00:39:08+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 4
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 7

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=257.59%, PF=3.29, timing_p=0.309, q80=1.000, repairs=0, embargo=5, data_end=2026-09-28
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=174.34%, PF=8.49, timing_p=0.247, q80=1.000, repairs=3, embargo=5, data_end=2026-09-30
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=118.90%, PF=2.60, timing_p=0.247, q80=1.000, repairs=0, embargo=5, data_end=2026-09-28
- 탈락 한화오션 (042660.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=27.20%, PF=1.60, timing_p=0.185, q80=1.000, repairs=3, embargo=5, data_end=2026-09-30
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=24.01%, PF=13.91, timing_p=0.062, q80=1.000, repairs=2, embargo=5, data_end=2026-09-30
- 관찰 Caterpillar (CAT): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=27.38%, PF=2.74, timing_p=0.444, q80=1.000, repairs=0, embargo=5, data_end=2026-09-28
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=21.46%, PF=1.49, timing_p=0.296, q80=1.000, repairs=3, embargo=5, data_end=2026-09-30
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=37.94%, PF=1.89, timing_p=0.432, q80=1.000, repairs=0, embargo=5, data_end=2026-09-28
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=1.000, repairs=0, embargo=5, data_end=2026-09-28
- B Berkshire (BRK-B): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=14.90%, PF=965.53, timing_p=0.037, q80=1.000, repairs=0, embargo=5, data_end=2026-09-28
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.53%, PF=4.90, timing_p=0.185, q80=1.000, repairs=0, embargo=5, data_end=2026-09-28
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=13.39%, PF=2.74, timing_p=0.272, q80=1.000, repairs=1, embargo=5, data_end=2026-09-30
- B NAVER (035420.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=19.32%, PF=4.22, timing_p=0.148, q80=1.000, repairs=1, embargo=5, data_end=2026-09-30
- 탈락 ExxonMobil (XOM): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=15.39%, PF=nan, timing_p=0.173, q80=1.000, repairs=0, embargo=5, data_end=2026-09-28
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=6.19%, PF=2.94, timing_p=0.235, q80=1.000, repairs=0, embargo=5, data_end=2026-09-28
