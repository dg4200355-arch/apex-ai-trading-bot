# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-10-05T00:03:31+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 4
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 6

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=287.44%, PF=3.60, timing_p=0.346, q80=1.000, repairs=0, embargo=5, data_end=2026-10-02
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=174.34%, PF=8.49, timing_p=0.247, q80=1.000, repairs=3, embargo=5, data_end=2026-10-02
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=126.30%, PF=2.67, timing_p=0.222, q80=1.000, repairs=0, embargo=5, data_end=2026-10-02
- 탈락 한화오션 (042660.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=72.66%, PF=nan, timing_p=0.012, q80=0.988, repairs=3, embargo=5, data_end=2026-10-02
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=21.71%, PF=7.19, timing_p=0.086, q80=1.000, repairs=2, embargo=5, data_end=2026-10-02
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=25.26%, PF=2.63, timing_p=0.383, q80=1.000, repairs=0, embargo=5, data_end=2026-10-02
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=16.24%, PF=1.41, timing_p=0.284, q80=1.000, repairs=3, embargo=5, data_end=2026-10-02
- B Berkshire (BRK-B): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=13.86%, PF=902.35, timing_p=0.049, q80=1.000, repairs=0, embargo=5, data_end=2026-10-02
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.53%, PF=4.90, timing_p=0.173, q80=1.000, repairs=0, embargo=5, data_end=2026-10-02
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=15.39%, PF=3.41, timing_p=0.247, q80=1.000, repairs=1, embargo=5, data_end=2026-10-02
- B Chevron (CVX): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.64%, PF=16.03, timing_p=0.160, q80=1.000, repairs=0, embargo=5, data_end=2026-10-02
- B Coca-Cola (KO): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=12.86%, PF=19.95, timing_p=0.049, q80=1.000, repairs=0, embargo=5, data_end=2026-10-02
- 탈락 Salesforce (CRM): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=10.54%, PF=1.84, timing_p=0.148, q80=1.000, repairs=0, embargo=5, data_end=2026-10-02
- 탈락 ExxonMobil (XOM): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=15.39%, PF=nan, timing_p=0.222, q80=1.000, repairs=0, embargo=5, data_end=2026-10-02
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=6.19%, PF=2.94, timing_p=0.235, q80=1.000, repairs=0, embargo=5, data_end=2026-10-02
