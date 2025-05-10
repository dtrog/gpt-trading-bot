# exchange.py
import requests

class KrakenFuturesAPI:
    def __init__(self):
        self.base_url = "https://futures.kraken.com/derivatives/api/v3"

    def fetch_tickers(self):
        response = requests.get(f"{self.base_url}/tickers")
        response.raise_for_status()
        tickers = response.json()["tickers"]
        return {t["symbol"]: t for t in tickers if t.get("tag") == "perpetual" and not t.get("suspended")}

    def place_order(self, symbol, direction):
        print(f"[LIVE TRADING] Would place {direction} order for {symbol} (Not implemented for security reasons)")
