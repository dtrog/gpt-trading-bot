from config import MOMENTUM_THRESHOLD, MIN_VOLUME, FUNDING_RATE_SHORT, FUNDING_RATE_LONG

def detect_signals(tickers, limit=None, override_threshold=None):
    threshold = override_threshold if override_threshold is not None else MOMENTUM_THRESHOLD
    candidates = []

    for symbol, data in tickers.items():
        try:
            change = float(data.get("change24h", 0))
            volume = float(data.get("volumeQuote", 0))
            funding = float(data.get("fundingRate", 0))

            if volume < MIN_VOLUME:
                continue

            # Determine trade type
            scalp = abs(change) >= threshold
            direction = None

            if change > 0 and funding < FUNDING_RATE_LONG:
                direction = "long"
            elif change < 0 and funding > FUNDING_RATE_SHORT:
                direction = "short"

            if direction:
                candidates.append((symbol, direction, abs(change), scalp))
        except:
            continue

    candidates.sort(key=lambda x: -x[2])
    if limit:
        candidates = candidates[:limit]

    return {
        symbol: {
            "direction": direction,
            "leverage": 50 if scalp else 10,
            "scalp": scalp
        }
        for symbol, direction, _, scalp in candidates
    }