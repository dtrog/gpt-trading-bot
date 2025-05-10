# config.py
SLEEP_DELAY = 5  # seconds
SIMULATION_MODE = True
STARTING_CAPITAL = 10000
MAX_POSITIONS = 15

# Strategy thresholds
MOMENTUM_THRESHOLD = 7.0  # % gain over 24h
MIN_VOLUME = 50000  # USD equivalent
STOP_LOSS_PCT = 0.03
TAKE_PROFIT_PCT = 0.07
TRADING_FEE = 0.0005  # 0.05%
FUNDING_RATE_ESTIMATE = 0.0002  # 0.02% per hour
FUNDING_RATE_SHORT = 0.001    # avoid shorting when it's too costly
FUNDING_RATE_LONG = 0.001     # avoid longing when it's too crowded
