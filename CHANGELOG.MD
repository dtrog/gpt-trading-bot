# Changelog

## [v0.2.0] - 2025-05-11

### Added
- Shorting support with momentum + funding filter
- Trailing stop logic for both long and short positions
- Cooldown period to avoid immediate re-entry after exit
- Signal prioritization by 24h momentum, capped at MAX_POSITIONS
- Per-trade dynamic leverage selection via strategy logic

### Changed
- ROE and PnL now account for fees and estimated funding cost
- Terminal UI sorted alphabetically by ticker
- Entry and exit messages added with:
  - Color-coded rows (green/red/yellow)
  - Blinking message for take profit hits
  - 3-second visibility timer
- Leverage and stop info shown per position in curses UI

### Fixed
- Prevented crashes due to missing tickers or zero prices
- Improved spacing/alignment in curses terminal output

## [0.3.0] - 2025-05-11

### Added
- Session timer showing runtime.
- Scalping vs. swing open PnL breakdown in header.
- Per-position duration (HH:MM:SS) column.
- Interactive `q`-quit flow: summary and forced exit handling.
- Slash placeholders for inactive SL/TS columns.

### Fixed
- UI column alignment across all displays.
- Syntax errors in trailing stop activation logic.
- Logging enhanced for UI loop exceptions.

### Changed
- Adaptive scaling variables moved to `settings.json`.
- Merged SL/TP logic with breakeven and trailing activation.
