# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-10-02T00:59:22+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 4
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 5

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=283.71%, PF=3.58, timing_p=0.309, q80=1.000, repairs=0, embargo=5, data_end=2026-09-30
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=174.34%, PF=8.49, timing_p=0.247, q80=1.000, repairs=3, embargo=5, data_end=2026-10-02
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=118.56%, PF=2.60, timing_p=0.247, q80=1.000, repairs=0, embargo=5, data_end=2026-09-30
- 탈락 한화오션 (042660.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=72.66%, PF=nan, timing_p=0.012, q80=0.494, repairs=3, embargo=5, data_end=2026-10-02
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=21.71%, PF=7.19, timing_p=0.086, q80=1.000, repairs=2, embargo=5, data_end=2026-10-02
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=23.21%, PF=2.53, timing_p=0.444, q80=1.000, repairs=0, embargo=5, data_end=2026-09-30
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=16.24%, PF=1.41, timing_p=0.284, q80=1.000, repairs=3, embargo=5, data_end=2026-10-02
- B Berkshire (BRK-B): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=14.22%, PF=924.18, timing_p=0.049, q80=1.000, repairs=0, embargo=5, data_end=2026-09-30
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.53%, PF=4.90, timing_p=0.148, q80=1.000, repairs=0, embargo=5, data_end=2026-09-30
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=15.39%, PF=3.41, timing_p=0.247, q80=1.000, repairs=1, embargo=5, data_end=2026-10-02
- B Chevron (CVX): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.64%, PF=16.03, timing_p=0.148, q80=1.000, repairs=0, embargo=5, data_end=2026-09-30
- 탈락 Salesforce (CRM): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=12.22%, PF=1.96, timing_p=0.136, q80=1.000, repairs=0, embargo=5, data_end=2026-09-30
- 탈락 ExxonMobil (XOM): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=15.39%, PF=nan, timing_p=0.210, q80=1.000, repairs=0, embargo=5, data_end=2026-09-30
- 탈락 Johnson&Johnson (JNJ): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=12.79%, PF=3.63, timing_p=0.790, q80=1.000, repairs=0, embargo=5, data_end=2026-09-30
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=6.19%, PF=2.94, timing_p=0.210, q80=1.000, repairs=0, embargo=5, data_end=2026-09-30
