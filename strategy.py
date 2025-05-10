# strategy.py
from config import MOMENTUM_THRESHOLD, MIN_VOLUME

def detect_signals(tickers):
    signals = {}
    for symbol, data in tickers.items():
        try:
            change = float(data.get("change24h", 0))
            volume = float(data.get("volumeQuote", 0))
            if change > MOMENTUM_THRESHOLD and volume > MIN_VOLUME:
                signals[symbol] = "long"
        except Exception:
            continue
    return signals
