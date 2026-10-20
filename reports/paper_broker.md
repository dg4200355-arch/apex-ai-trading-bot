# APEX raw-execution shadow paper broker

- broker: paper-broker-1.4-raw-execution
- price_basis: RAW_EXECUTION
- live orders: NEVER
- fee/slippage each side: 0.15% / 0.05%
- dividends: credited as gross virtual cash (taxes ignored)
- stock splits: integer-safe quantity/cost-basis adjustment; ambiguous fractional cases fail closed
- validation/promotion remains independent from broker P/L

## Accounts

- KR KRW: equity=9,854,899.12, cash=9,854,899.12, return=-1.45%, max_dd=-2.39%, halt=False, positions=0, trades=4, dividends=0.00
- US USD: equity=10,144.15, cash=10,144.15, return=1.44%, max_dd=-0.09%, halt=False, positions=0, trades=2, dividends=0.00

## This run

- order/action events: 1
- 2026-10-20 KR 035420.KS BUY BLOCKED NOT_FROZEN_VERIFIED
