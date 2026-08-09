import pandas as pd

from tools.portfolio_gate import correlation_components, choose_cluster_leaders


def test_high_correlation_pairs_form_one_cluster():
    tickers = ["A", "B", "C"]
    pairs = [("A", "B", 0.91, 200), ("B", "C", 0.85, 200), ("A", "C", 0.60, 200)]
    comps = correlation_components(tickers, pairs)
    assert sorted(comps) == [["A", "B", "C"]]


def test_low_correlation_names_stay_separate():
    tickers = ["A", "B", "C"]
    pairs = [("A", "B", 0.50, 200), ("B", "C", 0.40, 200)]
    comps = correlation_components(tickers, pairs)
    assert sorted(comps) == [["A"], ["B"], ["C"]]


def promo(code, forward, boot, pf, mdd, trades):
    return pd.Series({
        "코드": code,
        "최종상태": "전진검증완료",
        "동결검증": "FROZEN_VERIFIED",
        "전진누적수익": forward,
        "부트스트랩양수확률": boot,
        "PF": pf,
        "전진MDD": mdd,
        "완료거래": trades,
    })


def test_one_leader_is_selected_from_validated_cluster():
    comps = [["V", "MA"]]
    promo_map = {
        "V": promo("V", 0.12, 0.82, 1.4, -0.05, 7),
        "MA": promo("MA", 0.09, 0.90, 1.8, -0.04, 9),
    }
    leaders = choose_cluster_leaders(comps, promo_map)
    assert leaders["V"] == "V"
    assert leaders["MA"] == "V"


def test_non_validated_member_cannot_be_cluster_leader():
    comps = [["A", "B"]]
    a = promo("A", 0.20, 0.95, 2.0, -0.03, 10)
    a["최종상태"] = "관찰중"
    promo_map = {"A": a, "B": promo("B", 0.05, 0.75, 1.2, -0.08, 5)}
    leaders = choose_cluster_leaders(comps, promo_map)
    assert leaders["A"] == "B"
    assert leaders["B"] == "B"
