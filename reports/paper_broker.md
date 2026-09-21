# APEX raw-execution shadow paper broker

- broker: paper-broker-1.4-raw-execution
- price_basis: RAW_EXECUTION
- live orders: NEVER
- fee/slippage each side: 0.15% / 0.05%
- dividends: credited as gross virtual cash (taxes ignored)
- stock splits: integer-safe quantity/cost-basis adjustment; ambiguous fractional cases fail closed
- validation/promotion remains independent from broker P/L

## Accounts

- KR KRW: equity=10,019,072.06, cash=7,660,872.06, return=0.19%, max_dd=-0.98%, halt=False, positions=1, trades=1, dividends=0.00
- US USD: equity=10,000.00, cash=10,000.00, return=0.00%, max_dd=0.00%, halt=False, positions=0, trades=0, dividends=0.00

## This run

- order/action events: 2
- 2026-09-21 KR 055550.KS SELL FILLED SIGNAL_EXIT
- 2026-09-21 KR 068270.KS BUY FILLED SIGNAL_ENTRY
