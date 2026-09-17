# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-09-17T23:36:48+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 6
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 37
- total repaired OHLC bars: 86
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 7

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=245.18%, PF=3.16, timing_p=0.321, q80=0.988, repairs=0, embargo=5, data_end=2026-09-17
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=197.94%, PF=9.46, timing_p=0.247, q80=0.941, repairs=3, embargo=5, data_end=2026-09-17
- 탈락 AMD (AMD): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=115.62%, PF=41.13, timing_p=0.099, q80=0.941, repairs=0, embargo=5, data_end=2026-09-17
- B Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=43.06%, PF=4.14, timing_p=0.296, q80=0.988, repairs=1, embargo=5, data_end=2026-09-17
- 탈락 한화오션 (042660.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=27.20%, PF=1.60, timing_p=0.198, q80=0.941, repairs=3, embargo=5, data_end=2026-09-17
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=42.11%, PF=1.97, timing_p=0.383, q80=1.000, repairs=0, embargo=5, data_end=2026-09-17
- 탈락 Salesforce (CRM): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=19.16%, PF=3.26, timing_p=0.062, q80=0.941, repairs=0, embargo=5, data_end=2026-09-17
- 탈락 한화에어로스페이스 (012450.KS): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=15.76%, PF=1.48, timing_p=0.247, q80=0.941, repairs=2, embargo=5, data_end=2026-09-17
- 탈락 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=20.40%, PF=1.47, timing_p=0.321, q80=0.988, repairs=3, embargo=5, data_end=2026-09-17
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=26.00%, PF=nan, timing_p=0.074, q80=0.941, repairs=2, embargo=5, data_end=2026-09-17
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=0.941, repairs=0, embargo=5, data_end=2026-09-17
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.53%, PF=4.90, timing_p=0.148, q80=0.941, repairs=0, embargo=5, data_end=2026-09-17
- B NAVER (035420.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=21.86%, PF=6.36, timing_p=0.148, q80=0.941, repairs=1, embargo=5, data_end=2026-09-17
- 탈락 Broadcom (AVGO): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=12.53%, PF=1.31, timing_p=0.407, q80=1.000, repairs=0, embargo=5, data_end=2026-09-17
- 관찰 신한지주 (055550.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=14.56%, PF=2.69, timing_p=0.494, q80=1.000, repairs=2, embargo=5, data_end=2026-09-17
