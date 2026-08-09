# APEX diagnostic

```text
.....................................F...                                [100%]
=================================== FAILURES ===================================
_____________________ test_legacy_price_basis_is_rejected ______________________

    def test_legacy_price_basis_is_rejected():
        state = pb.new_broker_state("2026-08-09T00:00:00+00:00")
        errors = bh.validate_state(state, pd.DataFrame())
        assert "price-basis-not-raw-execution" in errors
>       assert "broker-version-not-raw-execution" in errors
E       AssertionError: assert 'broker-version-not-raw-execution' in ['price-basis-not-raw-execution']

tests/test_broker_health.py:25: AssertionError
=========================== short test summary info ============================
FAILED tests/test_broker_health.py::test_legacy_price_basis_is_rejected - AssertionError: assert 'broker-version-not-raw-execution' in ['price-basis-not-raw-execution']
1 failed, 40 passed in 2.22s
```

- compile_exit: 0
- tests_exit: 1
