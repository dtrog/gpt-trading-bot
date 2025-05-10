# strategy.py
from config import MOMENTUM_THRESHOLD, MIN_VOLUME, FUNDING_RATE_SHORT, FUNDING_RATE_LONG

# Example logic — conservative for volatile assets, higher for large caps
def decide_leverage(symbol, data):
    vol = float(data.get("volatility24h", 0))  # or derive from price range
    funding = float(data.get("fundingRate", 0))

    # Default conservative leverage
    if "BTC" in symbol or "ETH" in symbol:
        return 10 if vol > 5 else 20
    elif funding > 0.01:
        return 5  # lower leverage when funding is expensive
    else:
        return 15

def detect_signals(tickers, limit=None):
    candidates = []

    for symbol, data in tickers.items():
        try:
            change = float(data.get("change24h", 0))
            volume = float(data.get("volumeQuote", 0))
            funding = float(data.get("fundingRate", 0))

            if volume < MIN_VOLUME:
                continue

            # Long signal
            if change > MOMENTUM_THRESHOLD and funding < FUNDING_RATE_LONG:
                candidates.append((symbol, "long", change))

            # Short signal
            elif change < -MOMENTUM_THRESHOLD and funding > FUNDING_RATE_SHORT:
                candidates.append((symbol, "short", abs(change)))  # abs(change) for sorting

        except Exception:
            continue

    # Sort strongest moves first
    candidates.sort(key=lambda x: -x[2])
    if limit:
        candidates = candidates[:limit]

    return {symbol: (direction, decide_leverage(symbol, data)) for symbol, direction, _ in candidates}
