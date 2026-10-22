# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-10-22T00:05:19+00:00
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

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=256.73%, PF=3.48, timing_p=0.395, q80=1.000, repairs=0, embargo=5, data_end=2026-10-20
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=122.19%, PF=2.53, timing_p=0.210, q80=1.000, repairs=0, embargo=5, data_end=2026-10-20
- 탈락 삼성물산 (028260.KS): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=66.41%, PF=1.84, timing_p=0.099, q80=1.000, repairs=1, embargo=5, data_end=2026-10-21
- 탈락 한화오션 (042660.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=72.66%, PF=nan, timing_p=0.012, q80=0.494, repairs=3, embargo=5, data_end=2026-10-21
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=27.11%, PF=2.49, timing_p=0.309, q80=1.000, repairs=0, embargo=5, data_end=2026-10-20
- B Eli Lilly (LLY): strategy=AI {"threshold": 0.52}, TEST=25.15%, PF=2.85, timing_p=0.099, q80=1.000, repairs=0, embargo=5, data_end=2026-10-20
- B Qualcomm (QCOM): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=38.08%, PF=1.78, timing_p=0.123, q80=1.000, repairs=0, embargo=5, data_end=2026-10-20
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=20.00%, PF=1.48, timing_p=0.235, q80=1.000, repairs=3, embargo=5, data_end=2026-10-21
- 탈락 한화에어로스페이스 (012450.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=16.50%, PF=1.53, timing_p=0.185, q80=1.000, repairs=2, embargo=5, data_end=2026-10-21
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=1.000, repairs=0, embargo=5, data_end=2026-10-20
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=19.38%, PF=6.64, timing_p=0.222, q80=1.000, repairs=1, embargo=5, data_end=2026-10-21
- 탈락 Berkshire (BRK-B): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=20.66%, PF=nan, timing_p=0.012, q80=0.494, repairs=0, embargo=5, data_end=2026-10-20
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=9.04%, PF=3.78, timing_p=0.296, q80=1.000, repairs=0, embargo=5, data_end=2026-10-20
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=14.55%, PF=2.70, timing_p=0.173, q80=1.000, repairs=2, embargo=5, data_end=2026-10-21
- 탈락 LG에너지솔루션 (373220.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=18.23%, PF=2.83, timing_p=0.148, q80=1.000, repairs=1, embargo=5, data_end=2026-10-21
