# APEX raw-execution shadow paper broker

- broker: paper-broker-1.4-raw-execution
- price_basis: RAW_EXECUTION
- live orders: NEVER
- fee/slippage each side: 0.15% / 0.05%
- dividends: credited as gross virtual cash (taxes ignored)
- stock splits: integer-safe quantity/cost-basis adjustment; ambiguous fractional cases fail closed
- validation/promotion remains independent from broker P/L

## Accounts

- KR KRW: equity=9,994,919.66, cash=7,650,119.66, return=-0.05%, max_dd=-1.21%, halt=False, positions=1, trades=2, dividends=0.00
- US USD: equity=10,000.00, cash=10,000.00, return=0.00%, max_dd=0.00%, halt=False, positions=0, trades=0, dividends=0.00

## This run

- order/action events: 3
- 2026-09-30 KR 068270.KS SELL FILLED VERIFICATION_REVOKED
- 2026-09-30 KR 068270.KS BUY BLOCKED NOT_FROZEN_VERIFIED
- 2026-09-30 KR 035420.KS BUY FILLED SIGNAL_ENTRY
