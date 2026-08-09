import pandas as pd
import pytest

from tools.stress_confirm import parse_frozen_choice


def test_parse_frozen_choice_uses_exact_primary_metadata():
    row = pd.Series({
        "선택전략": "반전",
        "전략파라미터": '{"bb": 0.25, "rsi": 40}',
        "데이터시작일": "2021-08-09",
        "데이터기준일": "2026-08-07",
    })
    kind, params, start, cutoff = parse_frozen_choice(row)
    assert kind == "반전"
    assert params == {"bb": 0.25, "rsi": 40}
    assert start == pd.Timestamp("2021-08-09")
    assert cutoff == pd.Timestamp("2026-08-07")


def test_missing_frozen_parameters_are_rejected():
    row = pd.Series({
        "선택전략": "반전",
        "데이터시작일": "2021-08-09",
        "데이터기준일": "2026-08-07",
    })
    with pytest.raises(ValueError, match="freeze metadata missing"):
        parse_frozen_choice(row)


def test_invalid_primary_window_is_rejected():
    row = pd.Series({
        "선택전략": "추세",
        "전략파라미터": '{"fast": 8, "slow": 55, "rsi_max": 76, "vol_min": 0.65}',
        "데이터시작일": "2026-08-08",
        "데이터기준일": "2026-08-07",
    })
    with pytest.raises(ValueError, match="invalid primary data window"):
        parse_frozen_choice(row)
