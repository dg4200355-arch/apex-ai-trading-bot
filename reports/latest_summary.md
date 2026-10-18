# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-10-18T23:27:03+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 6
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 5

## Top candidates

- 탈락 삼성전기 (009150.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=454.72%, PF=12.32, timing_p=0.346, q80=1.000, repairs=4, embargo=5, data_end=2026-10-16
- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=292.97%, PF=3.92, timing_p=0.358, q80=1.000, repairs=0, embargo=5, data_end=2026-10-16
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=102.34%, PF=2.34, timing_p=0.284, q80=1.000, repairs=0, embargo=5, data_end=2026-10-16
- 탈락 삼성물산 (028260.KS): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=54.74%, PF=1.69, timing_p=0.284, q80=1.000, repairs=1, embargo=5, data_end=2026-10-16
- 탈락 NVIDIA (NVDA): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=43.53%, PF=nan, timing_p=0.012, q80=0.494, repairs=0, embargo=5, data_end=2026-10-16
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=26.87%, PF=2.46, timing_p=0.370, q80=1.000, repairs=0, embargo=5, data_end=2026-10-16
- B Qualcomm (QCOM): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=38.08%, PF=1.78, timing_p=0.123, q80=1.000, repairs=0, embargo=5, data_end=2026-10-16
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=18.67%, PF=1.46, timing_p=0.210, q80=1.000, repairs=3, embargo=5, data_end=2026-10-16
- 탈락 신한지주 (055550.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=18.54%, PF=5.18, timing_p=0.123, q80=1.000, repairs=2, embargo=5, data_end=2026-10-16
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=1.000, repairs=0, embargo=5, data_end=2026-10-16
- 탈락 Berkshire (BRK-B): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=22.91%, PF=nan, timing_p=0.012, q80=0.494, repairs=0, embargo=5, data_end=2026-10-16
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=15.16%, PF=5.05, timing_p=0.148, q80=1.000, repairs=0, embargo=5, data_end=2026-10-16
- 탈락 AbbVie (ABBV): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=15.29%, PF=6.55, timing_p=0.309, q80=1.000, repairs=0, embargo=5, data_end=2026-10-16
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=14.30%, PF=3.01, timing_p=0.259, q80=1.000, repairs=1, embargo=5, data_end=2026-10-16
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=8.81%, PF=3.72, timing_p=0.235, q80=1.000, repairs=0, embargo=5, data_end=2026-10-16
