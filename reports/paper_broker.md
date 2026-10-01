# APEX raw-execution shadow paper broker

- broker: paper-broker-1.4-raw-execution
- price_basis: RAW_EXECUTION
- live orders: NEVER
- fee/slippage each side: 0.15% / 0.05%
- dividends: credited as gross virtual cash (taxes ignored)
- stock splits: integer-safe quantity/cost-basis adjustment; ambiguous fractional cases fail closed
- validation/promotion remains independent from broker P/L

## Accounts

- KR KRW: equity=9,950,519.66, cash=7,650,119.66, return=-0.49%, max_dd=-1.29%, halt=False, positions=1, trades=2, dividends=0.00
- US USD: equity=10,000.00, cash=10,000.00, return=0.00%, max_dd=0.00%, halt=False, positions=0, trades=0, dividends=0.00

## This run

- order/action events: 0
