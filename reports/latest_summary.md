# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-10-15T00:00:32+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 5
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 8

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=274.29%, PF=3.53, timing_p=0.333, q80=1.000, repairs=0, embargo=5, data_end=2026-10-13
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=115.48%, PF=2.59, timing_p=0.272, q80=1.000, repairs=0, embargo=5, data_end=2026-10-13
- 탈락 삼성물산 (028260.KS): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=54.74%, PF=1.69, timing_p=0.333, q80=1.000, repairs=1, embargo=5, data_end=2026-10-14
- 탈락 신한지주 (055550.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=23.43%, PF=56.82, timing_p=0.062, q80=1.000, repairs=2, embargo=5, data_end=2026-10-14
- B Qualcomm (QCOM): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=33.23%, PF=1.67, timing_p=0.136, q80=1.000, repairs=0, embargo=5, data_end=2026-10-13
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=16.01%, PF=1.41, timing_p=0.247, q80=1.000, repairs=3, embargo=5, data_end=2026-10-14
- B 셀트리온 (068270.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=22.48%, PF=7.00, timing_p=0.062, q80=1.000, repairs=5, embargo=5, data_end=2026-10-14
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=18.76%, PF=4.27, timing_p=0.136, q80=1.000, repairs=2, embargo=5, data_end=2026-10-14
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=1.000, repairs=0, embargo=5, data_end=2026-10-13
- 관찰 Caterpillar (CAT): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=18.40%, PF=2.05, timing_p=0.481, q80=1.000, repairs=0, embargo=5, data_end=2026-10-13
- B Berkshire (BRK-B): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=12.51%, PF=819.74, timing_p=0.062, q80=1.000, repairs=0, embargo=5, data_end=2026-10-13
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.53%, PF=4.90, timing_p=0.148, q80=1.000, repairs=0, embargo=5, data_end=2026-10-13
- B Chevron (CVX): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.64%, PF=16.03, timing_p=0.123, q80=1.000, repairs=0, embargo=5, data_end=2026-10-13
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=8.96%, PF=3.76, timing_p=0.148, q80=1.000, repairs=0, embargo=5, data_end=2026-10-13
- 탈락 AbbVie (ABBV): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=13.34%, PF=5.91, timing_p=0.346, q80=1.000, repairs=0, embargo=5, data_end=2026-10-13
