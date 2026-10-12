# APEX raw-execution shadow paper broker

- broker: paper-broker-1.4-raw-execution
- price_basis: RAW_EXECUTION
- live orders: NEVER
- fee/slippage each side: 0.15% / 0.05%
- dividends: credited as gross virtual cash (taxes ignored)
- stock splits: integer-safe quantity/cost-basis adjustment; ambiguous fractional cases fail closed
- validation/promotion remains independent from broker P/L

## Accounts

- KR KRW: equity=9,973,850.01, cash=7,583,150.01, return=-0.26%, max_dd=-1.29%, halt=False, positions=1, trades=3, dividends=0.00
- US USD: equity=10,123.38, cash=7,599.64, return=1.23%, max_dd=-0.09%, halt=False, positions=1, trades=1, dividends=0.00

## This run

- order/action events: 0
