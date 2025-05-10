# bot.py
import time
from exchange import KrakenFuturesAPI
from strategy import detect_signals
from simulator import Portfolio
from config import SLEEP_DELAY, SIMULATION_MODE, STARTING_CAPITAL

# Initialize components
api = KrakenFuturesAPI()
portfolio = Portfolio(initial_cash=STARTING_CAPITAL)

print("Starting trading bot... (Simulation Mode: {} | Initial Cash: ${})".format(SIMULATION_MODE, STARTING_CAPITAL))

while True:
    try:
        tickers = api.fetch_tickers()
        signals = detect_signals(tickers)

        for symbol, signal in signals.items():
            if SIMULATION_MODE:
                portfolio.execute_trade(symbol, signal, tickers[symbol])
            else:
                api.place_order(symbol, signal)

        if SIMULATION_MODE:
            portfolio.update_positions(tickers)
            portfolio.log_status()

    except Exception as e:
        print("Error during execution:", e)

    time.sleep(SLEEP_DELAY)
