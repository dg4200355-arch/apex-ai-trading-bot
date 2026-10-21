# APEX autonomous validation summary

- engine_version: 8.5-frozen-primary
- scan_mode: FULL80
- run_at_utc: 2026-10-21T00:00:34+00:00
- universe: 80
- result_rows: 80
- valid-data normal rejections: 7
- true data/engine errors: 0
- tickers with isolated OHLC repairs: 36
- total repaired OHLC bars: 85
- selection split: 75% boundary with 5-bar purge/embargo
- A-grade passed after global correction: 0
- watch-or-better: 4

## Top candidates

- 탈락 Micron (MU): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=277.72%, PF=3.85, timing_p=0.370, q80=1.000, repairs=0, embargo=5, data_end=2026-10-19
- 탈락 AMD (AMD): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=114.80%, PF=2.47, timing_p=0.247, q80=1.000, repairs=0, embargo=5, data_end=2026-10-19
- 탈락 삼성물산 (028260.KS): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=60.22%, PF=1.76, timing_p=0.173, q80=1.000, repairs=1, embargo=5, data_end=2026-10-20
- 탈락 Caterpillar (CAT): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=25.20%, PF=2.31, timing_p=0.370, q80=1.000, repairs=0, embargo=5, data_end=2026-10-19
- B Qualcomm (QCOM): strategy=추세 {"fast": 8, "rsi_max": 82, "slow": 55, "vol_min": 0.8}, TEST=38.08%, PF=1.78, timing_p=0.123, q80=1.000, repairs=0, embargo=5, data_end=2026-10-19
- B 삼성중공업 (010140.KS): strategy=추세 {"fast": 21, "rsi_max": 74, "slow": 200, "vol_min": 0.7}, TEST=17.47%, PF=1.44, timing_p=0.222, q80=1.000, repairs=3, embargo=5, data_end=2026-10-20
- 탈락 POSCO홀딩스 (005490.KS): strategy=돌파 {"lookback": 20, "vol": 0.9}, TEST=19.38%, PF=6.64, timing_p=0.160, q80=1.000, repairs=1, embargo=5, data_end=2026-10-20
- 탈락 Amazon (AMZN): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=25.19%, PF=nan, timing_p=0.049, q80=1.000, repairs=0, embargo=5, data_end=2026-10-19
- 탈락 Berkshire (BRK-B): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=21.75%, PF=nan, timing_p=0.012, q80=0.988, repairs=0, embargo=5, data_end=2026-10-19
- 탈락 AbbVie (ABBV): strategy=돌파 {"lookback": 55, "vol": 1.0}, TEST=17.23%, PF=7.19, timing_p=0.284, q80=1.000, repairs=0, embargo=5, data_end=2026-10-19
- B Visa (V): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=10.06%, PF=4.08, timing_p=0.222, q80=1.000, repairs=0, embargo=5, data_end=2026-10-19
- 탈락 Apple (AAPL): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=13.92%, PF=4.74, timing_p=0.185, q80=1.000, repairs=0, embargo=5, data_end=2026-10-19
- 탈락 기아 (000270.KS): strategy=반전 {"bb": 0.1, "rsi": 35}, TEST=14.24%, PF=2.62, timing_p=0.185, q80=1.000, repairs=2, embargo=5, data_end=2026-10-20
- 탈락 ExxonMobil (XOM): strategy=반전 {"bb": 0.25, "rsi": 40}, TEST=15.39%, PF=nan, timing_p=0.284, q80=1.000, repairs=0, embargo=5, data_end=2026-10-19
- 탈락 Alphabet (GOOGL): strategy=추세 {"fast": 8, "rsi_max": 76, "slow": 55, "vol_min": 0.65}, TEST=21.89%, PF=1.53, timing_p=0.593, q80=1.000, repairs=0, embargo=5, data_end=2026-10-19
