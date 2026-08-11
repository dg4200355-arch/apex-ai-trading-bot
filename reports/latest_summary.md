# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-08-11T22:11:33+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 12
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 4

## Top candidates

- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=189.88%, PF=8.48, timing_p=0.259, q80=1.000, repairs=3, embargo=5, data_end=2026-08-11
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=186.94%, PF=3.39, timing_p=0.136, q80=1.000, repairs=0, embargo=5, data_end=2026-08-11
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=61.55%, PF=5.21, timing_p=0.432, q80=1.000, repairs=0, embargo=5, data_end=2026-08-11
- 탈락 Broadcom (AVGO): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=37.46%, PF=1.68, timing_p=0.284, q80=1.000, repairs=0, embargo=5, data_end=2026-08-11
- 탈락 Micron (MU): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=44.37%, PF=nan, timing_p=0.222, q80=1.000, repairs=0, embargo=5, data_end=2026-08-11
- 탈락 하나금융지주 (086790.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=23.07%, PF=157.66, timing_p=0.457, q80=1.000, repairs=2, embargo=5, data_end=2026-08-11
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=37.05%, PF=1.76, timing_p=0.506, q80=1.000, repairs=0, embargo=5, data_end=2026-08-11
- 탈락 신한지주 (055550.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=23.92%, PF=nan, timing_p=0.074, q80=1.000, repairs=2, embargo=5, data_end=2026-08-11
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.074, q80=1.000, repairs=0, embargo=5, data_end=2026-08-11
- 탈락 한화오션 (042660.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=22.29%, PF=1.47, timing_p=0.198, q80=1.000, repairs=3, embargo=5, data_end=2026-08-11
- 탈락 ExxonMobil (XOM): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=21.21%, PF=nan, timing_p=0.123, q80=1.000, repairs=0, embargo=5, data_end=2026-08-11
- 탈락 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=19.52%, PF=1.46, timing_p=0.309, q80=1.000, repairs=3, embargo=5, data_end=2026-08-11
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=12.11%, PF=4.69, timing_p=0.086, q80=1.000, repairs=0, embargo=5, data_end=2026-08-11
- B Chevron (CVX): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=14.64%, PF=16.03, timing_p=0.123, q80=1.000, repairs=0, embargo=5, data_end=2026-08-11
- 탈락 삼성전기 (009150.KS): strategy=AI {"threshold": 0.56}, TEST=11.21%, PF=13.35, timing_p=0.296, q80=1.000, repairs=4, embargo=5, data_end=2026-08-11
