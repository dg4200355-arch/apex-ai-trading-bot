# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-11-20T02:28:34+00:00
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

- 탈락 삼성전기 (009150.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=337.41%, PF=9.06, timing_p=0.074, q80=0.912, repairs=4, embargo=5, data_end=2026-11-20
- 탈락 한화오션 (042660.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=72.66%, PF=nan, timing_p=0.012, q80=0.912, repairs=3, embargo=5, data_end=2026-11-20
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=73.94%, PF=1.93, timing_p=0.395, q80=1.000, repairs=0, embargo=5, data_end=2026-11-19
- 탈락 삼성물산 (028260.KS): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=70.43%, PF=1.90, timing_p=0.123, q80=0.912, repairs=1, embargo=5, data_end=2026-11-20
- 탈락 삼성중공업 (010140.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=30.11%, PF=7.14, timing_p=0.062, q80=0.912, repairs=3, embargo=5, data_end=2026-11-20
- B Salesforce (CRM): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=31.68%, PF=2.32, timing_p=0.037, q80=0.912, repairs=0, embargo=5, data_end=2026-11-19
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=29.41%, PF=2.75, timing_p=0.160, q80=0.917, repairs=0, embargo=5, data_end=2026-11-19
- B 셀트리온 (068270.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=20.82%, PF=6.61, timing_p=0.136, q80=0.912, repairs=5, embargo=5, data_end=2026-11-20
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=20.45%, PF=5.56, timing_p=0.136, q80=0.912, repairs=2, embargo=5, data_end=2026-11-20
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=19.38%, PF=6.64, timing_p=0.185, q80=0.988, repairs=1, embargo=5, data_end=2026-11-20
- 탈락 Berkshire (BRK-B): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=18.71%, PF=nan, timing_p=0.025, q80=0.912, repairs=0, embargo=5, data_end=2026-11-19
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=0.912, repairs=0, embargo=5, data_end=2026-11-19
- 탈락 HLB (028300.KQ): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=11.35%, PF=nan, timing_p=0.272, q80=1.000, repairs=7, embargo=5, data_end=2026-11-20
- 탈락 Micron (MU): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=18.45%, PF=3.21, timing_p=0.630, q80=1.000, repairs=0, embargo=5, data_end=2026-11-19
- 탈락 HD현대중공업 (329180.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=10.73%, PF=1.65, timing_p=0.259, q80=1.000, repairs=2, embargo=5, data_end=2026-11-20
