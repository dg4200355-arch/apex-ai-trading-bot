# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-09-22T23:42:05+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 5
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 38
- total repaired OHLC bars: 87
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 8

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=226.20%, PF=3.03, timing_p=0.321, q80=1.000, repairs=0, embargo=5, data_end=2026-09-22
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=197.94%, PF=9.46, timing_p=0.235, q80=1.000, repairs=3, embargo=5, data_end=2026-09-22
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=94.15%, PF=2.34, timing_p=0.321, q80=1.000, repairs=0, embargo=5, data_end=2026-09-22
- B Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=40.73%, PF=4.00, timing_p=0.284, q80=1.000, repairs=0, embargo=5, data_end=2026-09-22
- 탈락 한화오션 (042660.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=27.20%, PF=1.60, timing_p=0.222, q80=1.000, repairs=3, embargo=5, data_end=2026-09-22
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=43.91%, PF=2.00, timing_p=0.321, q80=1.000, repairs=0, embargo=5, data_end=2026-09-22
- 탈락 Salesforce (CRM): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=17.75%, PF=2.90, timing_p=0.074, q80=1.000, repairs=0, embargo=5, data_end=2026-09-22
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=20.40%, PF=1.47, timing_p=0.296, q80=1.000, repairs=3, embargo=5, data_end=2026-09-22
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=26.00%, PF=nan, timing_p=0.086, q80=1.000, repairs=2, embargo=5, data_end=2026-09-22
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=1.000, repairs=0, embargo=5, data_end=2026-09-22
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.53%, PF=4.90, timing_p=0.148, q80=1.000, repairs=0, embargo=5, data_end=2026-09-22
- B Berkshire (BRK-B): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=13.29%, PF=867.81, timing_p=0.037, q80=1.000, repairs=0, embargo=5, data_end=2026-09-22
- B NAVER (035420.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=21.86%, PF=6.36, timing_p=0.160, q80=1.000, repairs=1, embargo=5, data_end=2026-09-22
- B 셀트리온 (068270.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=18.80%, PF=5.48, timing_p=0.062, q80=1.000, repairs=5, embargo=5, data_end=2026-09-22
- B Chevron (CVX): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.64%, PF=16.03, timing_p=0.148, q80=1.000, repairs=0, embargo=5, data_end=2026-09-22
