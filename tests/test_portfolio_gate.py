from tools.portfolio_gate import correlation_components


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
