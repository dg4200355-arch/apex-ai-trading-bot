# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-09-13T23:17:39+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 10
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 7

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=234.46%, PF=3.08, timing_p=0.309, q80=1.000, repairs=0, embargo=5, data_end=2026-09-11
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=197.94%, PF=9.46, timing_p=0.247, q80=1.000, repairs=3, embargo=5, data_end=2026-09-11
- 탈락 한화오션 (042660.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=96.47%, PF=nan, timing_p=0.025, q80=0.988, repairs=3, embargo=5, data_end=2026-09-11
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=100.88%, PF=2.39, timing_p=0.185, q80=1.000, repairs=0, embargo=5, data_end=2026-09-11
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=47.41%, PF=4.39, timing_p=0.333, q80=1.000, repairs=0, embargo=5, data_end=2026-09-11
- 탈락 Salesforce (CRM): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=22.86%, PF=4.75, timing_p=0.049, q80=0.988, repairs=0, embargo=5, data_end=2026-09-11
- B POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=32.43%, PF=24.68, timing_p=0.210, q80=1.000, repairs=1, embargo=5, data_end=2026-09-11
- 탈락 하나금융지주 (086790.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=23.07%, PF=157.66, timing_p=0.346, q80=1.000, repairs=2, embargo=5, data_end=2026-09-11
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=40.33%, PF=1.91, timing_p=0.457, q80=1.000, repairs=0, embargo=5, data_end=2026-09-11
- 탈락 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=17.91%, PF=1.42, timing_p=0.321, q80=1.000, repairs=3, embargo=5, data_end=2026-09-11
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=26.00%, PF=nan, timing_p=0.074, q80=1.000, repairs=2, embargo=5, data_end=2026-09-11
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=0.988, repairs=0, embargo=5, data_end=2026-09-11
- 탈락 한화에어로스페이스 (012450.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=13.01%, PF=1.39, timing_p=0.247, q80=1.000, repairs=2, embargo=5, data_end=2026-09-11
- 관찰 신한지주 (055550.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=17.14%, PF=2.95, timing_p=0.432, q80=1.000, repairs=2, embargo=5, data_end=2026-09-11
- 관찰 Johnson&Johnson (JNJ): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=16.76%, PF=9.16, timing_p=0.864, q80=1.000, repairs=0, embargo=5, data_end=2026-09-11
