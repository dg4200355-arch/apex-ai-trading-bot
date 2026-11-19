# APEX portfolio concentration gate

- gate: portfolio-gate-1.1-cluster-leader
- tracked: 14
- portfolio-allowed: 0
- high-correlation candidates: 4

Correlation warning threshold: 0.80 using at least 120 common daily returns.
If several members of one high-correlation cluster become individually forward-validated, exactly one leader is selected using forward evidence only.
This stage never places orders.

## Status

- Chevron (CVX): cluster=C1, leader=-, max_corr=0.867 vs ExxonMobil, risk=⚠️, allowed=❌, waiting=동결재검증, 전진검증
- Visa (V): cluster=C2, leader=-, max_corr=0.876 vs Mastercard, risk=⚠️, allowed=❌, waiting=전진검증
- Mastercard (MA): cluster=C2, leader=-, max_corr=0.876 vs Visa, risk=⚠️, allowed=❌, waiting=전진검증
- AbbVie (ABBV): cluster=C3, leader=-, max_corr=0.530 vs Johnson&Johnson, risk=-, allowed=❌, waiting=전진검증
- 신한지주 (055550.KS): cluster=C4, leader=-, max_corr=0.419 vs 셀트리온, risk=-, allowed=❌, waiting=동결재검증, 전진검증
- Caterpillar (CAT): cluster=C5, leader=-, max_corr=0.018 vs Eli Lilly, risk=-, allowed=❌, waiting=동결재검증, 전진검증
- Berkshire (BRK-B): cluster=C6, leader=-, max_corr=0.429 vs Mastercard, risk=-, allowed=❌, waiting=동결재검증, 전진검증
- 셀트리온 (068270.KS): cluster=C7, leader=-, max_corr=0.419 vs 신한지주, risk=-, allowed=❌, waiting=전진검증
- NAVER (035420.KS): cluster=C8, leader=-, max_corr=0.335 vs 셀트리온, risk=-, allowed=❌, waiting=동결재검증, 전진검증
- Coca-Cola (KO): cluster=C9, leader=-, max_corr=0.404 vs Johnson&Johnson, risk=-, allowed=❌, waiting=동결재검증, 전진검증
- Johnson&Johnson (JNJ): cluster=C10, leader=-, max_corr=0.530 vs AbbVie, risk=-, allowed=❌, waiting=동결재검증, 전진검증
- Eli Lilly (LLY): cluster=C11, leader=-, max_corr=0.478 vs Johnson&Johnson, risk=-, allowed=❌, waiting=동결재검증, 전진검증
- Walmart (WMT): cluster=C12, leader=-, max_corr=0.386 vs Coca-Cola, risk=-, allowed=❌, waiting=전진검증
- ExxonMobil (XOM): cluster=C1, leader=-, max_corr=0.867 vs Chevron, risk=⚠️, allowed=❌, waiting=동결재검증, 전진검증
