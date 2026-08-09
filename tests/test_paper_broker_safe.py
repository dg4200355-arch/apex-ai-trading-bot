from tools import paper_broker_safe as safe


def test_execution_error_gate_detects_only_error_status():
    rows = [
        {"상태": "FILLED", "코드": "A"},
        {"상태": "BLOCKED", "코드": "B"},
        {"상태": "ERROR", "코드": "C"},
    ]
    errors = safe.execution_errors(rows)
    assert len(errors) == 1
    assert errors[0]["코드"] == "C"


def test_no_execution_errors_is_commit_safe():
    assert safe.execution_errors([{"상태": "FILLED"}, {"상태": "BLOCKED"}]) == []
