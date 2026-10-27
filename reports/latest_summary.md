# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-10-27T00:40:04+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 5
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 7

## Top candidates

- 탈락 삼성전기 (009150.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=389.71%, PF=9.46, timing_p=0.247, q80=0.988, repairs=4, embargo=5, data_end=2026-10-27
- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=220.85%, PF=3.24, timing_p=0.358, q80=1.000, repairs=0, embargo=5, data_end=2026-10-23
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=90.71%, PF=2.16, timing_p=0.346, q80=1.000, repairs=0, embargo=5, data_end=2026-10-23
- 탈락 한화오션 (042660.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=72.66%, PF=nan, timing_p=0.012, q80=0.247, repairs=3, embargo=5, data_end=2026-10-27
- 탈락 삼성물산 (028260.KS): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=66.41%, PF=1.84, timing_p=0.086, q80=0.790, repairs=1, embargo=5, data_end=2026-10-27
- 탈락 NVIDIA (NVDA): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=43.53%, PF=nan, timing_p=0.012, q80=0.247, repairs=0, embargo=5, data_end=2026-10-23
- B 에코프로 (086520.KQ): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=50.51%, PF=2.61, timing_p=0.210, q80=0.988, repairs=1, embargo=5, data_end=2026-10-27
- 탈락 한화에어로스페이스 (012450.KS): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=29.37%, PF=2.22, timing_p=0.099, q80=0.790, repairs=2, embargo=5, data_end=2026-10-27
- 탈락 삼성중공업 (010140.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=30.11%, PF=7.14, timing_p=0.049, q80=0.564, repairs=3, embargo=5, data_end=2026-10-27
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=29.41%, PF=2.75, timing_p=0.272, q80=0.988, repairs=0, embargo=5, data_end=2026-10-23
- B Eli Lilly (LLY): strategy=AI {"threshold": 0.56}, TEST=27.64%, PF=4.78, timing_p=0.049, q80=0.564, repairs=0, embargo=5, data_end=2026-10-23
- B 셀트리온 (068270.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=22.48%, PF=7.00, timing_p=0.099, q80=0.790, repairs=5, embargo=5, data_end=2026-10-27
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=20.45%, PF=5.56, timing_p=0.148, q80=0.988, repairs=2, embargo=5, data_end=2026-10-27
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=0.564, repairs=0, embargo=5, data_end=2026-10-23
- 탈락 Berkshire (BRK-B): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=21.61%, PF=nan, timing_p=0.012, q80=0.247, repairs=0, embargo=5, data_end=2026-10-23
