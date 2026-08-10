# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-08-10T22:06:51+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 12
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 37
- total repaired OHLC bars: 86
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 4

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=207.52%, PF=3.04, timing_p=0.395, q80=1.000, repairs=0, embargo=5, data_end=2026-08-10
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=189.88%, PF=8.48, timing_p=0.259, q80=1.000, repairs=3, embargo=5, data_end=2026-08-10
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=191.35%, PF=3.42, timing_p=0.099, q80=0.988, repairs=0, embargo=5, data_end=2026-08-10
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=62.73%, PF=5.28, timing_p=0.407, q80=1.000, repairs=0, embargo=5, data_end=2026-08-10
- 탈락 Broadcom (AVGO): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=31.30%, PF=1.59, timing_p=0.321, q80=1.000, repairs=0, embargo=5, data_end=2026-08-10
- 탈락 하나금융지주 (086790.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=23.07%, PF=157.65, timing_p=0.457, q80=1.000, repairs=2, embargo=5, data_end=2026-08-10
- 탈락 삼성중공업 (010140.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=26.16%, PF=1.59, timing_p=0.247, q80=1.000, repairs=3, embargo=5, data_end=2026-08-10
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=35.55%, PF=1.74, timing_p=0.506, q80=1.000, repairs=0, embargo=5, data_end=2026-08-10
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=32.24%, PF=24.57, timing_p=0.222, q80=1.000, repairs=1, embargo=5, data_end=2026-08-10
- 탈락 SK하이닉스 (000660.KS): strategy=AI {"threshold": 0.64}, TEST=29.46%, PF=1.86, timing_p=0.543, q80=1.000, repairs=3, embargo=5, data_end=2026-08-10
- 탈락 신한지주 (055550.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=23.92%, PF=nan, timing_p=0.074, q80=0.988, repairs=2, embargo=5, data_end=2026-08-10
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.074, q80=0.988, repairs=0, embargo=5, data_end=2026-08-10
- 탈락 한화오션 (042660.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=22.29%, PF=1.47, timing_p=0.198, q80=1.000, repairs=3, embargo=5, data_end=2026-08-10
- 탈락 ExxonMobil (XOM): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=21.21%, PF=nan, timing_p=0.123, q80=0.988, repairs=0, embargo=5, data_end=2026-08-10
- 탈락 한화에어로스페이스 (012450.KS): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=11.41%, PF=1.34, timing_p=0.272, q80=1.000, repairs=2, embargo=5, data_end=2026-08-10
