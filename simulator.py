import logging
import csv
import curses
import time
import json
from pathlib import Path

# Configure logging
logging.basicConfig(filename='simulation.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')
SETTINGS_PATH = "settings.json"

def load_settings():
    try:
        with open(SETTINGS_PATH) as f:
            return json.load(f)
    except:
        return {}

class Portfolio:
    def __init__(self, initial_cash, max_open_positions=10):
        self.cash = initial_cash
        self.positions = {}
        self.trade_history = []
        self.screen = None
        self.default_leverage = 20
        self.max_open_positions = max_open_positions
        self.cooldowns = {}
        self.cooldown_seconds = 300
        self.flash_message = ""
        self.flash_timer = 0
        self.settings = load_settings()
        self.session_start = time.time()
        self.last_tickers = {}

    def execute_trade(self, symbol, direction, data, leverage=None, scalp=False, simulate=True):
        now = time.time()
        if len(self.positions) >= self.max_open_positions:
            return
        if symbol in self.cooldowns and now - self.cooldowns[symbol] < self.cooldown_seconds:
            return

        price = float(data.get("markPrice", 0))
        if not price or symbol in self.positions:
            return

        leverage = leverage or self.default_leverage
        if self.settings.get("ADAPTIVE_SCALING", True):
            cap_pct = self.settings.get("SCALPING_CAPITAL_PCT", 0.05) if scalp else self.settings.get("NORMAL_TRADE_CAPITAL_PCT", 0.1)
        else:
            cap_pct = 0.05
        trade_cash = self.cash * cap_pct
        size = trade_cash / price
        cost = trade_cash * (1 + self.settings.get("TRADING_FEE", 0.0006))
        if self.cash < cost:
            return

        if scalp:
            sl_pct = 0.005
            tp_pct = 0.018
        else:
            sl_pct = self.settings.get("STOP_LOSS_PCT", 0.005) * (self.default_leverage / leverage)
            tp_pct = self.settings.get("TAKE_PROFIT_PCT", 0.018) * (self.default_leverage / leverage)
        ts_pct = self.settings.get("TRAIL_STOP_PCT", 0.003)

        self.cash -= cost
        self.positions[symbol] = {
            "entry_price": price,
            "open_time": now,
            "size": size,
            "direction": direction,
            "leverage": leverage,
            "hours_held": 0,
            "capital_used": cost,
            "max_price": price,
            "min_price": price,
            "stop_loss_pct": sl_pct,
            "take_profit_pct": tp_pct,
            "trail_offset_pct": ts_pct,
            "scalp": scalp,
            "breakeven_set": False,
            "trailing_active": False,
            "simulate": simulate
        }

        self.flash_message = f"Opened {symbol} {direction.upper()} @ {price:.4f}"
        self.flash_timer = 3
        logging.info(f"[SIM] Entered {direction} {symbol} @ {price:.4f} | Lev:{leverage}x SL:{sl_pct:.4f} TP:{tp_pct:.4f} TS:{ts_pct:.4f}")

    def update_positions(self, tickers):
        to_close = []
        open_lines = []

        for symbol in sorted(self.positions):
            pos = self.positions[symbol]
            data = tickers.get(symbol)
            if not data:
                continue
            price = float(data.get("markPrice", 0))
            if not price:
                continue

            direction = pos["direction"]
            entry = pos["entry_price"]
            pnl_pct = (price - entry) / entry if direction == "long" else (entry - price) / entry
            roe_pct = pnl_pct * pos["leverage"]
            pos["hours_held"] += 1/12

            if direction == "long":
                pos["max_price"] = max(pos["max_price"], price)
            else:
                pos["min_price"] = min(pos["min_price"], price)

            # Breakeven adjustment
            if pos["scalp"] and pnl_pct > 0 and not pos["breakeven_set"]:
                pos["stop_loss_pct"] = 0.0
                pos["breakeven_set"] = True
            # Trailing activation at 2% ROE
            if pos["scalp"] and roe_pct >= 0.02 and not pos["trailing_active"]:
                pos["take_profit_pct"] = None
                pos["stop_loss_pct"] = 0.0
                pos["trailing_active"] = True

            exit_reason = None
            if pos["trailing_active"]:
                if direction == "long" and price < pos["max_price"] * (1 - pos["trail_offset_pct"]):
                    exit_reason = "TRAILING STOP"
                if direction == "short" and price > pos["min_price"] * (1 + pos["trail_offset_pct"]):
                    exit_reason = "TRAILING STOP"
            else:
                if pnl_pct <= -pos["stop_loss_pct"]:
                    exit_reason = "STOP LOSS"
                if pos["take_profit_pct"] and pnl_pct >= pos["take_profit_pct"]:
                    exit_reason = "TAKE PROFIT"

            if exit_reason:
                capital_used = pos["capital_used"]
                fee_cost = self.settings.get("TRADING_FEE", 0.0006) * 2 * capital_used
                funding   = self.settings.get("FUNDING_RATE_ESTIMATE", 0.0002) * pos["hours_held"] * entry * pos["size"]
                gross     = pnl_pct * entry * pos["size"]
                net_pnl   = gross - fee_cost - funding
                self.cash += capital_used + net_pnl
                result = "profit" if net_pnl > 0 else "loss"
                self.flash_message = f"Closed {symbol} @ {price:.4f}: {net_pnl:+.2f}$ ({result})"
                self.flash_timer = 3
                logging.info(f"[SIM] Closed {symbol} @ {price:.4f} | {result.upper()} {net_pnl:.2f} USD | ROE:{roe_pct*100:.2f}%")
                self.trade_history.append({
                    "symbol": symbol,
                    "entry_price": entry,
                    "exit_price": price,
                    "capital_used": capital_used,
                    "gain": net_pnl,
                    "roe": roe_pct,
                    "result": result,
                    "exit_reason": exit_reason,
                    "scalp": pos["scalp"]
                })
                to_close.append(symbol)
            else:
                fee_cost = self.settings.get("TRADING_FEE", 0.0006) * 2 * pos["capital_used"]
                funding   = self.settings.get("FUNDING_RATE_ESTIMATE", 0.0002) * pos["hours_held"] * entry * pos["size"]
                gross     = pnl_pct * entry * pos["size"]
                net_pnl   = gross - fee_cost - funding
                open_lines.append((symbol, pos, roe_pct, pnl_pct, net_pnl, price))

        for s in to_close:
            del self.positions[s]

        if self.screen:
            # Session and PnL summary
            elapsed = time.time() - self.session_start
            hrs, rem  = divmod(int(elapsed), 3600)
            mins, secs = divmod(rem, 60)
            scalp_net = sum(l[4] for l in open_lines if l[1]["scalp"])
            swing_net = sum(l[4] for l in open_lines if not l[1]["scalp"])
            total_closed = len(self.trade_history)
            wins = sum(1 for t in self.trade_history if t["result"] == "profit")
            win_rate = (wins/total_closed*100) if total_closed else 0
            total_allocated = sum(l[1]["capital_used"] for l in open_lines)
            total_net = sum(l[4] for l in open_lines)

            self.screen.erase()
            rows, cols = self.screen.getmaxyx()
            self.screen.addstr(0, 0,
                f"Time {hrs:02d}:{mins:02d}:{secs:02d}  Cash:${self.cash:.2f}  Closed:{total_closed}  Win:{win_rate:5.2f}%")
            self.screen.addstr(1, 0,
                f"Alloc:${total_allocated:.2f}  OpenPnL:${total_net:.2f} (Scalp:${scalp_net:.2f} Swing:${swing_net:.2f})")

            if self.flash_timer > 0:
                clr = curses.color_pair(2 if "+" in self.flash_message else 1)
                self.screen.addstr(2, 0, self.flash_message, clr)
                self.flash_timer -= 1

            # column headers
            header = (
                f"{'SYMBOL':<14} {'DIR':<8} {'LEV':>5}  "
                f"{'ROE%':>7}  {'PnL%':>7}  {'Net$':>9}  "
                f"{'SL%':>6}  {'TP%':>6}  {'TS%':>6}  {'TYPE':>6}  {'DUR':>8}"
            )
            self.screen.addstr(3, 0, header, curses.color_pair(3))

            for idx, (symbol, pos, roe, pnl, net, price) in enumerate(open_lines[:rows-5]):
                sl_pct = pos["stop_loss_pct"] * 100
                tp_pct = (pos["take_profit_pct"] or 0) * 100
                ts_pct = pos["trail_offset_pct"] * 100
                                # display slash when SL removed or TS not active
                sl_disp = f"{sl_pct:>6.2f}%" if pos["stop_loss_pct"] != 0 else f"{'/':>7}"
                ts_disp = f"{ts_pct:>6.2f}%" if pos["trailing_active"] else f"{'/':>7}"

                trade_type = 'SCALP' if pos['scalp'] else 'SWING'
                # duration
                dur = time.time() - pos["open_time"]
                dh, dr = divmod(int(dur), 3600)
                dm, ds = divmod(dr, 60)
                dur_str = f"{dh:02d}:{dm:02d}:{ds:02d}"

                clr = curses.color_pair(2 if net > 0 else 1 if net < 0 else 3)
                line = (
                    f"{symbol:<14} {pos['direction']:<8} {pos['leverage']:>5}  "
                    f"{roe*100:>7.2f}%  {pnl*100:>7.2f}%  ${net:>7.2f}  "
                    f"{sl_disp}  {tp_pct:>6.2f}%  {ts_disp}  "
                    f"{trade_type:>6}  {dur_str:>8}"
                )
                self.screen.addstr(4 + idx, 0, line, clr)

            self.screen.refresh()
            time.sleep(self.settings.get("SLEEP_DELAY", 1))

    def _show_session_summary(self):
        # Force-close all open positions
        for symbol, pos in list(self.positions.items()):
            data  = self.last_tickers.get(symbol, {})
            price = float(data.get("markPrice", pos["entry_price"]))
            entry = pos["entry_price"]
            pnl_pct = (price-entry)/entry if pos["direction"]=="long" else (entry-price)/entry
            fee     = self.settings.get("TRADING_FEE",0.0006)*2*pos["capital_used"]
            funding = self.settings.get("FUNDING_RATE_ESTIMATE",0.0002)*pos["hours_held"]*entry*pos["size"]
            gross   = pnl_pct*entry*pos["size"]
            net     = gross-fee-funding
            self.cash += pos["capital_used"]+net
            result = "profit" if net>0 else "loss"
            self.trade_history.append({
                "symbol": symbol,
                "entry_price": entry,
                "exit_price": price,
                "capital_used": pos["capital_used"],
                "gain": net,
                "roe": pnl_pct*pos["leverage"],
                "result": result,
                "exit_reason": "FORCED EXIT",
                "scalp": pos["scalp"]
            })
            del self.positions[symbol]

        total = len(self.trade_history)
        wins  = sum(1 for t in self.trade_history if t["result"]=="profit")
        total_pnl = sum(t["gain"] for t in self.trade_history)
        avg_roe   = sum(t["roe"] for t in self.trade_history)/total if total else 0

        self.screen.erase()
        summary_lines = [
            "=== SESSION SUMMARY ===",
            f"Trades: {total}  Wins: {wins}  WinRate: {wins/total*100 if total else 0:.2f}%",
            f"Total PnL: ${total_pnl:.2f}  Final Cash: ${self.cash:.2f}",
            f"Avg ROE: {avg_roe*100:.2f}%",
            "Press 'q' again to exit"
        ]
        for i, text in enumerate(summary_lines):
            self.screen.addstr(i+2, 2, text, curses.color_pair(3))
        self.screen.refresh()

    def run_with_ui(self, tickers_generator):
        curses.wrapper(self._run_loop, tickers_generator)

    def _run_loop(self, stdscr, tickers_generator):
        self.screen = stdscr
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        stdscr.nodelay(True)
        try:
            curses.curs_set(0)
        except:
            pass
        while True:
            c = stdscr.getch()
            if c == ord('q'):
                self._show_session_summary()
                while True:
                    d = stdscr.getch()
                    if d == ord('q'):
                        return
            if c == ord('r'):
                self.settings = load_settings()
                self.flash_message = "[Reloaded settings.json]"
                self.flash_timer   = 3
            try:
                tickers = next(tickers_generator)
                self.last_tickers = tickers or {}
                self.update_positions(tickers or {})
            except StopIteration:
                break
            except Exception as e:
                import traceback
                logging.error("UI loop error: " + traceback.format_exc())
                break

    def summary_report(self):
        with open("trade_summary.csv", "w", newline="") as csvfile:
            fieldnames = ["symbol","entry_price","exit_price","capital_used","gain","roe","result","exit_reason","scalp"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for trade in self.trade_history:
                writer.writerow(trade)
        logging.info(f"Remaining Cash: ${self.cash:.2f}")
