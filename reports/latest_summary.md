# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-09-09T23:25:03+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 9
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 7

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=225.83%, PF=3.04, timing_p=0.284, q80=1.000, repairs=0, embargo=5, data_end=2026-09-09
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=197.94%, PF=9.46, timing_p=0.247, q80=1.000, repairs=3, embargo=5, data_end=2026-09-09
- 탈락 한화오션 (042660.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=96.47%, PF=nan, timing_p=0.025, q80=0.988, repairs=3, embargo=5, data_end=2026-09-09
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=52.27%, PF=4.67, timing_p=0.235, q80=1.000, repairs=0, embargo=5, data_end=2026-09-09
- 탈락 Salesforce (CRM): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=22.86%, PF=4.75, timing_p=0.049, q80=0.988, repairs=0, embargo=5, data_end=2026-09-09
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=47.14%, PF=2.05, timing_p=0.383, q80=1.000, repairs=0, embargo=5, data_end=2026-09-09
- 탈락 하나금융지주 (086790.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=23.07%, PF=157.65, timing_p=0.358, q80=1.000, repairs=2, embargo=5, data_end=2026-09-09
- 탈락 신한지주 (055550.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=21.67%, PF=3.45, timing_p=0.407, q80=1.000, repairs=2, embargo=5, data_end=2026-09-09
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=17.91%, PF=1.42, timing_p=0.309, q80=1.000, repairs=3, embargo=5, data_end=2026-09-09
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=26.00%, PF=nan, timing_p=0.074, q80=0.988, repairs=2, embargo=5, data_end=2026-09-09
- 관찰 Johnson&Johnson (JNJ): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=16.64%, PF=9.11, timing_p=0.827, q80=1.000, repairs=0, embargo=5, data_end=2026-09-09
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=10.54%, PF=4.22, timing_p=0.086, q80=0.988, repairs=0, embargo=5, data_end=2026-09-09
- B Chevron (CVX): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.64%, PF=16.03, timing_p=0.210, q80=1.000, repairs=0, embargo=5, data_end=2026-09-09
- 탈락 셀트리온 (068270.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=17.14%, PF=5.73, timing_p=0.086, q80=0.988, repairs=5, embargo=5, data_end=2026-09-09
- 탈락 ExxonMobil (XOM): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=15.39%, PF=nan, timing_p=0.222, q80=1.000, repairs=0, embargo=5, data_end=2026-09-09
