# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-10-29T01:07:23+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 7
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 5

## Top candidates

- 탈락 삼성전기 (009150.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=384.13%, PF=9.41, timing_p=0.235, q80=1.000, repairs=4, embargo=5, data_end=2026-10-29
- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=224.74%, PF=3.30, timing_p=0.333, q80=1.000, repairs=0, embargo=5, data_end=2026-10-27
- 탈락 한화오션 (042660.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=72.66%, PF=nan, timing_p=0.012, q80=0.329, repairs=3, embargo=5, data_end=2026-10-29
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=83.80%, PF=2.05, timing_p=0.321, q80=1.000, repairs=0, embargo=5, data_end=2026-10-27
- 탈락 삼성물산 (028260.KS): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=66.41%, PF=1.84, timing_p=0.099, q80=1.000, repairs=1, embargo=5, data_end=2026-10-29
- 탈락 삼성중공업 (010140.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=30.11%, PF=7.14, timing_p=0.049, q80=0.790, repairs=3, embargo=5, data_end=2026-10-29
- 탈락 한화에어로스페이스 (012450.KS): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=29.37%, PF=2.22, timing_p=0.111, q80=1.000, repairs=2, embargo=5, data_end=2026-10-29
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=29.41%, PF=2.75, timing_p=0.272, q80=1.000, repairs=0, embargo=5, data_end=2026-10-27
- B 셀트리온 (068270.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=22.48%, PF=7.00, timing_p=0.099, q80=1.000, repairs=5, embargo=5, data_end=2026-10-29
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=20.45%, PF=5.56, timing_p=0.148, q80=1.000, repairs=2, embargo=5, data_end=2026-10-29
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=0.790, repairs=0, embargo=5, data_end=2026-10-27
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=19.38%, PF=6.64, timing_p=0.173, q80=1.000, repairs=1, embargo=5, data_end=2026-10-29
- 탈락 HD현대중공업 (329180.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=10.73%, PF=1.65, timing_p=0.284, q80=1.000, repairs=2, embargo=5, data_end=2026-10-29
- 탈락 Berkshire (BRK-B): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=18.71%, PF=nan, timing_p=0.012, q80=0.329, repairs=0, embargo=5, data_end=2026-10-27
- 관찰 Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=8.38%, PF=3.59, timing_p=0.370, q80=1.000, repairs=0, embargo=5, data_end=2026-10-27
