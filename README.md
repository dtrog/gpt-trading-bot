# Kraken Futures Momentum Trading Bot

![Python](https://img.shields.io/badge/python-3.11-blue)
![Status](https://img.shields.io/badge/status-active-brightgreen)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)


This is a command-line trading bot for Kraken Futures that uses a momentum and scalping strategy to trade perpetual futures contracts.

## 📈 Strategy Overview

The bot identifies trading signals based on:
- **24h price momentum**: Targets assets with strong positive momentum.
- **Volume confirmation**: Ensures liquidity and tradeability.
- **Open interest (future improvement)**: Potential to filter pump-and-dump traps.

Once a signal is triggered:
- The bot enters a **long** position (shorting coming soon).
- Risk is limited to 5% of portfolio capital per trade.
- Positions are automatically closed based on:
  - **Stop-loss**: 3%
  - **Take-profit**: 7%
  - **Trailing time-based funding cost**

## ⚙️ Simulation Features

- Simulated trades track:
  - Entry & exit prices
  - Capital used
  - ROE %
  - Fees and funding costs
  - PnL and trade result

- Logs are saved in `simulation.log`
- Final trade report is exported to `trade_summary.csv`

## 🚀 Getting Started

### Requirements

- Python 3.11+
- Kraken Futures account and API credentials
- `pyenv` + `python-dotenv`

### Setup

```bash
chmod +x trading-bot-setup.sh
./trading-bot-setup.sh
```

Then:

```bash
cp .env.example .env
# Add your Kraken API key and secret
```

### Run

```bash
python bot.py
```

## 📦 Project Structure

- `bot.py`: Main execution loop
- `exchange.py`: API integration with Kraken
- `strategy.py`: Momentum detection logic
- `simulator.py`: Backtest engine with ROE, cost, and log tracking
- `config.py`: Parameters
- `.env`: Secure API keys
- `requirements.txt`: Python libraries
- `trading-bot-setup.sh`: Full setup script

---

This project is for educational use. Trading involves risk. Use responsibly.