# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-08-18T21:46:43+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 13
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 4

## Top candidates

- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=189.88%, PF=8.48, timing_p=0.259, q80=1.000, repairs=3, embargo=5, data_end=2026-08-14
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=164.20%, PF=3.08, timing_p=0.111, q80=0.912, repairs=0, embargo=5, data_end=2026-08-18
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=47.27%, PF=3.76, timing_p=0.481, q80=1.000, repairs=0, embargo=5, data_end=2026-08-18
- 탈락 Micron (MU): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=40.46%, PF=nan, timing_p=0.370, q80=1.000, repairs=0, embargo=5, data_end=2026-08-18
- 탈락 하나금융지주 (086790.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=23.07%, PF=157.66, timing_p=0.469, q80=1.000, repairs=2, embargo=5, data_end=2026-08-14
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=32.24%, PF=24.57, timing_p=0.222, q80=1.000, repairs=1, embargo=5, data_end=2026-08-14
- 탈락 한화에어로스페이스 (012450.KS): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=14.12%, PF=1.40, timing_p=0.235, q80=1.000, repairs=2, embargo=5, data_end=2026-08-14
- 탈락 신한지주 (055550.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=23.92%, PF=nan, timing_p=0.074, q80=0.912, repairs=2, embargo=5, data_end=2026-08-14
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.062, q80=0.912, repairs=0, embargo=5, data_end=2026-08-18
- 탈락 한화오션 (042660.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=22.29%, PF=1.47, timing_p=0.198, q80=1.000, repairs=3, embargo=5, data_end=2026-08-14
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=23.95%, PF=nan, timing_p=0.111, q80=0.912, repairs=2, embargo=5, data_end=2026-08-14
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=28.89%, PF=1.60, timing_p=0.617, q80=1.000, repairs=0, embargo=5, data_end=2026-08-18
- B Chevron (CVX): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.64%, PF=16.03, timing_p=0.148, q80=0.912, repairs=0, embargo=5, data_end=2026-08-18
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=12.11%, PF=4.69, timing_p=0.049, q80=0.912, repairs=0, embargo=5, data_end=2026-08-18
- 탈락 셀트리온 (068270.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=17.14%, PF=5.73, timing_p=0.086, q80=0.912, repairs=5, embargo=5, data_end=2026-08-14
