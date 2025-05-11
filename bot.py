
from simulator import Portfolio
from strategy import detect_signals
from exchange import KrakenFuturesAPI
from config import STARTING_CAPITAL, SLEEP_DELAY, MAX_POSITIONS, REAL_TRADING, DRY_RUN
from __version__ import __version__
import time
import logging

try:
    from config import DEBUG_NO_UI
except ImportError:
    DEBUG_NO_UI = False

print(f"GPT Trading Bot v{__version__}")
api = KrakenFuturesAPI()
portfolio = Portfolio(initial_cash=STARTING_CAPITAL, max_open_positions=MAX_POSITIONS)

def tickers_loop():
    while True:
        try:
            tickers = api.get_tickers()
            if not tickers:
                logging.warning("No tickers returned.")
                time.sleep(2)
                continue

            signals = detect_signals(tickers, limit=MAX_POSITIONS)
            for symbol, signal in signals.items():
                if symbol not in tickers:
                    continue
                portfolio.execute_trade(
                    symbol=symbol,
                    direction=signal["direction"],
                    data=tickers[symbol],
                    leverage=signal.get("leverage"),
                    scalp=signal.get("scalp", False),
                    simulate=not DRY_RUN
                )
            yield tickers
            time.sleep(SLEEP_DELAY)
        except Exception as e:
            logging.error(f"Error in tickers_loop: {e}")
            time.sleep(2)

try:
    if DEBUG_NO_UI:
        print("Running in debug mode (no curses UI)...")
        for _ in tickers_loop():
            tickers = api.get_tickers()
            if tickers:
                portfolio.update_positions(tickers)
    else:
        portfolio.run_with_ui(tickers_loop())

    portfolio.summary_report()
except ImportError as e:
    logging.error("ImportError: " + str(e))
    print("Failed to import module:", e)
except Exception as e:
    logging.error("Runtime error: " + str(e))
    print("Error:", e)
