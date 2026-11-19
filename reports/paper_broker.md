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
- US USD: equity=9,822.66, cash=9,822.66, return=-1.77%, max_dd=-3.96%, halt=False, positions=0, trades=7, dividends=0.00

## This run

- order/action events: 6
- 2026-11-19 US ABBV SELL FILLED SIGNAL_EXIT
- 2026-11-19 US JNJ SELL FILLED VERIFICATION_REVOKED
- 2026-11-19 US XOM SELL FILLED VERIFICATION_REVOKED
- 2026-11-19 US CVX BUY BLOCKED NOT_FROZEN_VERIFIED
- 2026-11-19 US JNJ BUY BLOCKED NOT_FROZEN_VERIFIED
- 2026-11-19 US XOM BUY BLOCKED NOT_FROZEN_VERIFIED
