# APEX portfolio concentration gate

- gate: portfolio-gate-1.0-correlation
- tracked: 3
- portfolio-allowed: 0
- high-correlation candidates: 2

Correlation warning threshold: 0.80 using at least 120 common daily returns.
High correlation is shown immediately, but it blocks portfolio use only when multiple members of the same cluster are individually forward-validated.
This stage never places orders.

## Status

- Chevron (CVX): cluster=C1, max_corr=-0.039 vs Mastercard, risk=-, allowed=❌, waiting=전진검증
- Visa (V): cluster=C2, max_corr=0.850 vs Mastercard, risk=⚠️, allowed=❌, waiting=전진검증
- Mastercard (MA): cluster=C2, max_corr=0.850 vs Visa, risk=⚠️, allowed=❌, waiting=전진검증
