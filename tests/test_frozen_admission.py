import pandas as pd

from tools.paper_forward import admission_matches, normalized_params


def test_normalized_params_ignores_json_key_order_only():
    a = '{"bb": 0.25, "rsi": 40}'
    b = '{"rsi": 40, "bb": 0.25}'
    assert normalized_params(a) == normalized_params(b)


def test_admission_matches_exact_strategy_and_parameters():
    state = {"전략": "반전", "전략파라미터": {"bb": 0.25, "rsi": 40}}
    row = pd.Series({"전략": "반전", "전략파라미터": '{"rsi": 40, "bb": 0.25}'})
    assert admission_matches(state, row)


def test_admission_rejects_parameter_drift():
    state = {"전략": "반전", "전략파라미터": {"bb": 0.25, "rsi": 40}}
    row = pd.Series({"전략": "반전", "전략파라미터": '{"bb": 0.18, "rsi": 40}'})
    assert not admission_matches(state, row)


def test_admission_rejects_strategy_family_drift():
    state = {"전략": "반전", "전략파라미터": {"bb": 0.25, "rsi": 40}}
    row = pd.Series({"전략": "추세", "전략파라미터": '{"bb": 0.25, "rsi": 40}'})
    assert not admission_matches(state, row)
