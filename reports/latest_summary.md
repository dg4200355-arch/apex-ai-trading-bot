# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-09-24T23:57:07+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 7
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 8

## Top candidates

- 탈락 삼성전기 (009150.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=449.61%, PF=11.94, timing_p=0.309, q80=1.000, repairs=4, embargo=5, data_end=2026-09-23
- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=232.95%, PF=3.12, timing_p=0.346, q80=1.000, repairs=0, embargo=5, data_end=2026-09-24
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=197.94%, PF=9.46, timing_p=0.247, q80=1.000, repairs=3, embargo=5, data_end=2026-09-23
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=106.90%, PF=2.48, timing_p=0.284, q80=1.000, repairs=0, embargo=5, data_end=2026-09-24
- B Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=40.45%, PF=3.99, timing_p=0.259, q80=1.000, repairs=0, embargo=5, data_end=2026-09-24
- 탈락 한화오션 (042660.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=27.20%, PF=1.60, timing_p=0.210, q80=1.000, repairs=3, embargo=5, data_end=2026-09-23
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=39.64%, PF=1.92, timing_p=0.432, q80=1.000, repairs=0, embargo=5, data_end=2026-09-24
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=18.62%, PF=1.43, timing_p=0.272, q80=1.000, repairs=3, embargo=5, data_end=2026-09-23
- 탈락 Salesforce (CRM): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=15.39%, PF=2.45, timing_p=0.074, q80=1.000, repairs=0, embargo=5, data_end=2026-09-24
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=26.00%, PF=nan, timing_p=0.086, q80=1.000, repairs=2, embargo=5, data_end=2026-09-23
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=1.000, repairs=0, embargo=5, data_end=2026-09-24
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.53%, PF=4.90, timing_p=0.148, q80=1.000, repairs=0, embargo=5, data_end=2026-09-24
- B Berkshire (BRK-B): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=13.68%, PF=891.28, timing_p=0.025, q80=0.988, repairs=0, embargo=5, data_end=2026-09-24
- B NAVER (035420.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=21.86%, PF=6.36, timing_p=0.136, q80=1.000, repairs=1, embargo=5, data_end=2026-09-23
- B 셀트리온 (068270.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=18.59%, PF=5.26, timing_p=0.074, q80=1.000, repairs=5, embargo=5, data_end=2026-09-23
