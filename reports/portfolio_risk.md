# APEX portfolio concentration gate

- gate: portfolio-gate-1.1-cluster-leader
- tracked: 8
- portfolio-allowed: 0
- high-correlation candidates: 2

Correlation warning threshold: 0.80 using at least 120 common daily returns.
If several members of one high-correlation cluster become individually forward-validated, exactly one leader is selected using forward evidence only.
This stage never places orders.

## Status

- Chevron (CVX): cluster=C1, leader=-, max_corr=0.003 vs Berkshire, risk=-, allowed=❌, waiting=전진검증
- Visa (V): cluster=C2, leader=-, max_corr=0.858 vs Mastercard, risk=⚠️, allowed=❌, waiting=전진검증
- Mastercard (MA): cluster=C2, leader=-, max_corr=0.858 vs Visa, risk=⚠️, allowed=❌, waiting=동결재검증, 전진검증
- AbbVie (ABBV): cluster=C3, leader=-, max_corr=0.244 vs Visa, risk=-, allowed=❌, waiting=전진검증
- 신한지주 (055550.KS): cluster=C4, leader=-, max_corr=0.434 vs 셀트리온, risk=-, allowed=❌, waiting=동결재검증, 전진검증
- Caterpillar (CAT): cluster=C5, leader=-, max_corr=-0.047 vs AbbVie, risk=-, allowed=❌, waiting=전진검증
- Berkshire (BRK-B): cluster=C6, leader=-, max_corr=0.384 vs Mastercard, risk=-, allowed=❌, waiting=전진검증
- 셀트리온 (068270.KS): cluster=C7, leader=-, max_corr=0.434 vs 신한지주, risk=-, allowed=❌, waiting=전진검증
