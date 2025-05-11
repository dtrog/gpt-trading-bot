# General trading settings
STARTING_CAPITAL = 10000
SLEEP_DELAY = 3  # seconds between each tick
MAX_POSITIONS = 20

# Scalping and position management
STOP_LOSS_PCT = 0.005      # 0.5%
TAKE_PROFIT_PCT = 0.018    # 1.8%
TRADING_FEE = 0.0006       # Round-trip fee estimate
FUNDING_RATE_ESTIMATE = 0.0002  # Hourly estimate

# Signal detection logic
MOMENTUM_THRESHOLD = 7.0   # % 24h change
MIN_VOLUME = STARTING_CAPITAL * 5         # USD
FUNDING_RATE_SHORT = 0.001
FUNDING_RATE_LONG = 0.001

# Execution modes
REAL_TRADING = False
DRY_RUN = False
DEBUG_NO_UI = False