# APEX raw-execution shadow paper broker

- broker: paper-broker-1.4-raw-execution
- price_basis: RAW_EXECUTION
- live orders: NEVER
- fee/slippage each side: 0.15% / 0.05%
- dividends: credited as gross virtual cash (taxes ignored)
- stock splits: integer-safe quantity/cost-basis adjustment; ambiguous fractional cases fail closed
- validation/promotion remains independent from broker P/L

## Accounts

- KR KRW: equity=9,959,094.19, cash=9,959,094.19, return=-0.41%, max_dd=-1.29%, halt=False, positions=0, trades=3, dividends=0.00
- US USD: equity=10,079.41, cash=7,599.64, return=0.79%, max_dd=-0.09%, halt=False, positions=1, trades=1, dividends=0.00

## This run

- order/action events: 1
- 2026-10-09 US ABBV BUY FILLED SIGNAL_ENTRY
