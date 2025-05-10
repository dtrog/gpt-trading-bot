# bot.py
import time
from __version__ import __version__
print(f"GPT Trading Bot v{__version__}")

from exchange import KrakenFuturesAPI
from strategy import detect_signals
from simulator import Portfolio
from config import SLEEP_DELAY, SIMULATION_MODE, STARTING_CAPITAL, MAX_POSITIONS

def tickers_loop(api, portfolio):
    while True:
        tickers = api.fetch_tickers()
        signals = detect_signals(tickers, limit=MAX_POSITIONS)

        for symbol, (direction, leverage) in signals.items():
            portfolio.execute_trade(symbol, direction, tickers[symbol], leverage=leverage)
        yield tickers
        time.sleep(SLEEP_DELAY)

# Initialize
api = KrakenFuturesAPI()
portfolio = Portfolio(initial_cash=STARTING_CAPITAL, max_open_positions=MAX_POSITIONS)

print(f"Starting trading bot... (Simulation Mode: {SIMULATION_MODE} | Initial Cash: ${STARTING_CAPITAL})")

if SIMULATION_MODE:
    portfolio.run_with_ui(tickers_loop(api, portfolio))
else:
    print("Live mode not implemented yet.")
