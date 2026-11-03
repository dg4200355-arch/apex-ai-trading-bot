# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-11-03T02:59:46+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 6
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 6

## Top candidates

- 탈락 삼성전기 (009150.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=375.10%, PF=9.35, timing_p=0.235, q80=1.000, repairs=4, embargo=5, data_end=2026-11-03
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=91.52%, PF=2.17, timing_p=0.259, q80=1.000, repairs=0, embargo=5, data_end=2026-11-02
- 탈락 한화오션 (042660.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=72.66%, PF=nan, timing_p=0.012, q80=0.494, repairs=3, embargo=5, data_end=2026-11-03
- 탈락 삼성물산 (028260.KS): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=66.41%, PF=1.84, timing_p=0.111, q80=1.000, repairs=1, embargo=5, data_end=2026-11-03
- 탈락 삼성중공업 (010140.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=30.11%, PF=7.14, timing_p=0.049, q80=0.988, repairs=3, embargo=5, data_end=2026-11-03
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=29.41%, PF=2.75, timing_p=0.222, q80=1.000, repairs=0, embargo=5, data_end=2026-11-02
- 탈락 한화에어로스페이스 (012450.KS): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=29.37%, PF=2.22, timing_p=0.086, q80=1.000, repairs=2, embargo=5, data_end=2026-11-03
- B Eli Lilly (LLY): strategy=AI {"threshold": 0.56}, TEST=23.82%, PF=4.57, timing_p=0.173, q80=1.000, repairs=0, embargo=5, data_end=2026-11-02
- 탈락 Micron (MU): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=34.06%, PF=nan, timing_p=0.333, q80=1.000, repairs=0, embargo=5, data_end=2026-11-02
- B 셀트리온 (068270.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=22.48%, PF=7.00, timing_p=0.086, q80=1.000, repairs=5, embargo=5, data_end=2026-11-03
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=20.45%, PF=5.56, timing_p=0.148, q80=1.000, repairs=2, embargo=5, data_end=2026-11-03
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=0.988, repairs=0, embargo=5, data_end=2026-11-02
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=19.38%, PF=6.64, timing_p=0.173, q80=1.000, repairs=1, embargo=5, data_end=2026-11-03
- 관찰 Merck (MRK): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=26.79%, PF=1.56, timing_p=0.556, q80=1.000, repairs=0, embargo=5, data_end=2026-11-02
- 탈락 Berkshire (BRK-B): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=18.71%, PF=nan, timing_p=0.012, q80=0.494, repairs=0, embargo=5, data_end=2026-11-02
