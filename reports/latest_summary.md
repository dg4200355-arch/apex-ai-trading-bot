# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-08-12T22:09:55+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 13
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 4

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=209.34%, PF=3.05, timing_p=0.383, q80=1.000, repairs=0, embargo=5, data_end=2026-08-12
- 탈락 LG이노텍 (011070.KS): strategy=돌파 {"lookback": 20, "vol": 1.15}, TEST=189.88%, PF=8.48, timing_p=0.272, q80=1.000, repairs=3, embargo=5, data_end=2026-08-12
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=184.07%, PF=3.33, timing_p=0.086, q80=0.988, repairs=0, embargo=5, data_end=2026-08-12
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=46.48%, PF=3.72, timing_p=0.506, q80=1.000, repairs=0, embargo=5, data_end=2026-08-12
- 탈락 하나금융지주 (086790.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=23.07%, PF=157.66, timing_p=0.469, q80=1.000, repairs=2, embargo=5, data_end=2026-08-12
- 탈락 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=24.42%, PF=1.53, timing_p=0.198, q80=1.000, repairs=3, embargo=5, data_end=2026-08-12
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=32.24%, PF=24.57, timing_p=0.235, q80=1.000, repairs=1, embargo=5, data_end=2026-08-12
- 탈락 신한지주 (055550.KS): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=23.92%, PF=nan, timing_p=0.074, q80=0.988, repairs=2, embargo=5, data_end=2026-08-12
- 탈락 한화오션 (042660.KS): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=22.29%, PF=1.47, timing_p=0.198, q80=1.000, repairs=3, embargo=5, data_end=2026-08-12
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.062, q80=0.988, repairs=0, embargo=5, data_end=2026-08-12
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=31.51%, PF=1.66, timing_p=0.556, q80=1.000, repairs=0, embargo=5, data_end=2026-08-12
- 탈락 ExxonMobil (XOM): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=21.21%, PF=nan, timing_p=0.123, q80=0.988, repairs=0, embargo=5, data_end=2026-08-12
- 탈락 한화에어로스페이스 (012450.KS): strategy=추세 {"fast": 21, "rsi_max": 76, "slow": 100, "vol_min": 0.65}, TEST=10.62%, PF=1.32, timing_p=0.235, q80=1.000, repairs=2, embargo=5, data_end=2026-08-12
- 탈락 Qualcomm (QCOM): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=25.96%, PF=1.58, timing_p=0.148, q80=0.988, repairs=0, embargo=5, data_end=2026-08-12
- 탈락 셀트리온 (068270.KS): strategy=반전 {"bb": 0.18, "rsi": 38}, TEST=17.76%, PF=5.88, timing_p=0.062, q80=0.988, repairs=5, embargo=5, data_end=2026-08-12
