# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-09-29T01:08:01+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 6
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 7

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=242.46%, PF=3.17, timing_p=0.346, q80=1.000, repairs=0, embargo=5, data_end=2026-09-25
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=197.94%, PF=9.46, timing_p=0.235, q80=0.941, repairs=3, embargo=5, data_end=2026-09-29
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=100.51%, PF=2.43, timing_p=0.346, q80=1.000, repairs=0, embargo=5, data_end=2026-09-25
- B Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=40.17%, PF=3.97, timing_p=0.272, q80=0.988, repairs=0, embargo=5, data_end=2026-09-25
- 탈락 한화오션 (042660.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=27.20%, PF=1.60, timing_p=0.185, q80=0.941, repairs=3, embargo=5, data_end=2026-09-29
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=21.46%, PF=1.49, timing_p=0.309, q80=1.000, repairs=3, embargo=5, data_end=2026-09-29
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=38.26%, PF=1.90, timing_p=0.420, q80=1.000, repairs=0, embargo=5, data_end=2026-09-25
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=26.00%, PF=nan, timing_p=0.074, q80=0.941, repairs=2, embargo=5, data_end=2026-09-29
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=0.941, repairs=0, embargo=5, data_end=2026-09-25
- B Berkshire (BRK-B): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=13.91%, PF=905.08, timing_p=0.025, q80=0.941, repairs=0, embargo=5, data_end=2026-09-25
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.53%, PF=4.90, timing_p=0.148, q80=0.941, repairs=0, embargo=5, data_end=2026-09-25
- B Chevron (CVX): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.64%, PF=16.03, timing_p=0.148, q80=0.941, repairs=0, embargo=5, data_end=2026-09-25
- B NAVER (035420.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=19.20%, PF=4.16, timing_p=0.160, q80=0.941, repairs=1, embargo=5, data_end=2026-09-29
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=12.86%, PF=2.61, timing_p=0.296, q80=1.000, repairs=1, embargo=5, data_end=2026-09-29
- 탈락 ExxonMobil (XOM): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=15.39%, PF=nan, timing_p=0.173, q80=0.941, repairs=0, embargo=5, data_end=2026-09-25
