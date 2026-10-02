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
- US USD: equity=9,990.61, cash=7,834.42, return=-0.09%, max_dd=-0.09%, halt=False, positions=1, trades=0, dividends=0.00

## This run

- order/action events: 2
- 2026-10-02 US V BUY FILLED SIGNAL_ENTRY
- 2026-10-02 US MA BUY BLOCKED NOT_FROZEN_VERIFIED
