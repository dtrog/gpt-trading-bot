# simulator.py
import logging
import csv
import curses
import time
from config import STOP_LOSS_PCT, TAKE_PROFIT_PCT, TRADING_FEE, FUNDING_RATE_ESTIMATE

logging.basicConfig(filename='simulation.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class Portfolio:
    def __init__(self, initial_cash, max_open_positions=10):
        self.cash = initial_cash
        self.positions = {}
        self.trade_history = []
        self.screen = None
        self.default_leverage = 20
        self.max_open_positions = max_open_positions
        self.cooldowns = {}
        self.cooldown_seconds = 300  # 5 minutes

    def execute_trade(self, symbol, direction, data, leverage=None):
        now = time.time()
        if len(self.positions) >= self.max_open_positions:
            return
        if symbol in self.cooldowns and now - self.cooldowns[symbol] < self.cooldown_seconds:
            return

        price = float(data.get("markPrice", 0))
        if not price or symbol in self.positions:
            return

        if leverage is None:
            leverage = self.default_leverage

        trade_cash = self.cash * 0.05
        size = trade_cash / price
        cost = trade_cash * (1 + TRADING_FEE)
        if self.cash < cost:
            return

        self.cash -= cost
        self.positions[symbol] = {
            "entry_price": price,
            "size": size,
            "direction": direction,
            "leverage": leverage,
            "hours_held": 0,
            "capital_used": cost,
            "max_price": price if direction == "long" else None,
            "min_price": price if direction == "short" else None
        }

        logging.info(f"[SIM] Entered {direction} {symbol} at {price:.4f} | Size: {size:.2f} | Capital Used: ${cost:.2f} | Leverage: {leverage}x")

        if self.screen:
            max_y, _ = self.screen.getmaxyx()
            msg = f"Opened {symbol[:10]} [{direction.upper()}] at {price:.4f} | Lev: {leverage}x"
            self.screen.addstr(max_y - 2, 0, msg, curses.color_pair(3))
            self.screen.clrtoeol()
            self.screen.refresh()
            time.sleep(3)
            self.screen.move(max_y - 2, 0)
            self.screen.clrtoeol()

    def update_positions(self, tickers):
        to_close = []
        lines = []

        for symbol, pos in self.positions.items():
            if symbol not in tickers:
                continue
            price = float(tickers[symbol].get("markPrice", 0))
            if not price:
                continue

            direction = pos["direction"]
            if direction == "long":
                pos["max_price"] = max(pos.get("max_price", price), price)
            elif direction == "short":
                pos["min_price"] = min(pos.get("min_price", price), price)

            entry = pos["entry_price"]
            size = pos["size"]
            capital_used = pos["capital_used"]
            leverage = pos["leverage"]
            pnl_pct = (price - entry) / entry if direction == "long" else (entry - price) / entry
            roe_pct = pnl_pct * leverage

            fee_cost = TRADING_FEE * 2 * capital_used
            funding_cost = FUNDING_RATE_ESTIMATE * pos["hours_held"] * entry * size
            gross_pnl = pnl_pct * entry * size
            net_pnl = gross_pnl - fee_cost - funding_cost

            lines.append((symbol, roe_pct, pnl_pct, price, capital_used, net_pnl, funding_cost, direction, leverage))

            # Exit logic
            trail_exit = False
            trailing_stop_pct = 0.003
            if direction == "long" and pos["max_price"] and price < pos["max_price"] * (1 - trailing_stop_pct):
                trail_exit = True
            if direction == "short" and pos["min_price"] and price > pos["min_price"] * (1 + trailing_stop_pct):
                trail_exit = True

            exit_reason = ""
            if pnl_pct <= -STOP_LOSS_PCT:
                exit_reason = "STOP LOSS"
            elif pnl_pct >= TAKE_PROFIT_PCT:
                exit_reason = "TAKE PROFIT"
            elif trail_exit:
                exit_reason = "TRAILING STOP"

            if exit_reason:
                self.cash += capital_used + net_pnl
                result = "profit" if net_pnl > 0 else "loss"
                self.cooldowns[symbol] = time.time()

                logging.info(
                    f"[SIM] Closed {symbol} at {price:.4f} with {result.upper()} ({exit_reason}) → Capital: ${capital_used:.2f}, "
                    f"Gain/Loss: ${net_pnl:.2f}, ROE: {roe_pct*100:.2f}%, Fees: ${fee_cost:.2f}, Funding: ${funding_cost:.2f}"
                )

                if self.screen:
                    max_y, _ = self.screen.getmaxyx()
                    msg = f"Closed {symbol[:10]} [{direction.upper()}] at {price:.4f} due to {exit_reason} | Result: {result.upper()}"
                    if result == "profit" and exit_reason == "TAKE PROFIT":
                        color = curses.color_pair(2) | curses.A_BLINK
                    elif result == "profit":
                        color = curses.color_pair(2)
                    else:
                        color = curses.color_pair(1)

                    self.screen.addstr(max_y - 2, 0, msg, color)
                    self.screen.clrtoeol()
                    self.screen.refresh()
                    time.sleep(3)
                    self.screen.move(max_y - 2, 0)
                    self.screen.clrtoeol()

                self.trade_history.append({
                    "symbol": symbol,
                    "entry_price": entry,
                    "exit_price": price,
                    "capital_used": capital_used,
                    "gain": net_pnl,
                    "roe": roe_pct,
                    "fees": fee_cost,
                    "funding": funding_cost,
                    "result": result,
                    "exit_reason": exit_reason
                })
                to_close.append(symbol)
            else:
                pos["hours_held"] += 1/12

        for symbol in to_close:
            del self.positions[symbol]

        if self.screen:
            lines.sort(key=lambda x: x[0])  # Alphabetical sort
            total_pnl = sum(p[5] for p in lines)
            total_allocated = sum(p[4] for p in lines)
            self.screen.erase()
            self.screen.addstr(0, 0, f"[SIM] Cash: ${self.cash:.2f} | Allocated: ${total_allocated:.2f} | Net P/L: ${total_pnl:.2f}")

            for idx, (symbol, roe, pnl, price, cap_used, net_pnl, funding_cost, direction, lev) in enumerate(lines[:self.screen.getmaxyx()[0] - 4]):
                color = (
                    curses.color_pair(1) if pnl <= -STOP_LOSS_PCT * 0.9 else
                    curses.color_pair(2) if pnl >= TAKE_PROFIT_PCT * 0.9 else
                    curses.color_pair(3)
                )
                self.screen.addstr(
                    idx + 2, 0,
                    f"{symbol[:10]:<10} [{direction.upper():<5}] Lev: {lev:>2}x | ROE: {roe*100:>7.2f}% | PnL: {pnl*100:>7.2f}% | "
                    f"Price: {price:>9.4f} | Cash: ${cap_used:>9.2f} | P/L: ${net_pnl:>8.2f} | Funding: ${funding_cost:>6.2f} "
                    f"| SL/TP: {STOP_LOSS_PCT*100:>4.1f}% / {TAKE_PROFIT_PCT*100:>4.1f}%",
                    color
                )
            self.screen.refresh()
            time.sleep(1)

    def run_with_ui(self, tickers_generator):
        curses.wrapper(self._run_loop, tickers_generator)

    def _run_loop(self, stdscr, tickers_generator):
        self.screen = stdscr
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        while True:
            try:
                tickers = next(tickers_generator)
                self.update_positions(tickers)
            except StopIteration:
                break
            except Exception as e:
                import traceback
                logging.error("Exception in update loop: " + traceback.format_exc())
                break

    def summary_report(self):
        with open("trade_summary.csv", "w", newline="") as csvfile:
            fieldnames = ["symbol", "entry_price", "exit_price", "capital_used", "gain", "roe", "fees", "funding", "result", "exit_reason"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for trade in self.trade_history:
                writer.writerow(trade)

        logging.info(f"Remaining Cash: ${self.cash:.2f}")
