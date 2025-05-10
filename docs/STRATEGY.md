# Strategy Explanation

This bot uses momentum-based trading logic to enter long positions on Kraken Futures. It scans 24h change and volume to find breakout candidates, enters with 5% of capital, and exits via stop-loss or take-profit.

## Key Concepts
- 24h Momentum
- Volume filter
- ROE-based closure
- Funding and fee awareness