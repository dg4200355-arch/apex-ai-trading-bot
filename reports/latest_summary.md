# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-10-15T23:45:02+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 5
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 37
- total repaired OHLC bars: 86
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 8

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=295.57%, PF=3.94, timing_p=0.346, q80=1.000, repairs=0, embargo=5, data_end=2026-10-15
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=110.06%, PF=2.48, timing_p=0.259, q80=1.000, repairs=0, embargo=5, data_end=2026-10-15
- 탈락 NVIDIA (NVDA): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=43.53%, PF=nan, timing_p=0.012, q80=0.494, repairs=0, embargo=5, data_end=2026-10-15
- 탈락 삼성물산 (028260.KS): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=54.74%, PF=1.69, timing_p=0.309, q80=1.000, repairs=1, embargo=5, data_end=2026-10-15
- 관찰 Merck (MRK): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=42.17%, PF=2.02, timing_p=0.395, q80=1.000, repairs=0, embargo=5, data_end=2026-10-15
- B Qualcomm (QCOM): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=38.08%, PF=1.78, timing_p=0.123, q80=1.000, repairs=0, embargo=5, data_end=2026-10-15
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=25.92%, PF=2.37, timing_p=0.383, q80=1.000, repairs=0, embargo=5, data_end=2026-10-15
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=18.79%, PF=1.47, timing_p=0.222, q80=1.000, repairs=3, embargo=5, data_end=2026-10-15
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=1.000, repairs=0, embargo=5, data_end=2026-10-15
- 탈락 Berkshire (BRK-B): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=21.20%, PF=nan, timing_p=0.012, q80=0.494, repairs=0, embargo=5, data_end=2026-10-15
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.53%, PF=4.90, timing_p=0.148, q80=1.000, repairs=0, embargo=5, data_end=2026-10-15
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=15.60%, PF=2.97, timing_p=0.210, q80=1.000, repairs=2, embargo=5, data_end=2026-10-15
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=14.30%, PF=3.01, timing_p=0.247, q80=1.000, repairs=1, embargo=5, data_end=2026-10-15
- B Chevron (CVX): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.64%, PF=16.03, timing_p=0.160, q80=1.000, repairs=0, embargo=5, data_end=2026-10-15
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=8.96%, PF=3.76, timing_p=0.198, q80=1.000, repairs=0, embargo=5, data_end=2026-10-15
