# APEX autonomous shadow paper broker

- broker: paper-broker-1.2-verification-exit
- live orders: NEVER
- position sizing: 25% max per entry
- cash reserve: 10%
- max positions per market: 3
- hard new-entry halt: -10% from account peak
- fee/slippage each side: 0.15% / 0.05%
- revoked verification forces next-open exit
- candidate promotion is independent from broker P/L

## Accounts

- KR KRW: equity=10,000,000.00, cash=10,000,000.00, return=0.00%, max_dd=0.00%, halt=False, positions=0, trades=0
- US USD: equity=10,000.00, cash=10,000.00, return=0.00%, max_dd=0.00%, halt=False, positions=0, trades=0

## This run

- order events: 0
