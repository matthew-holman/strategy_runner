# Stock Picker Bot

A Python-based experiment in building an automated trading research system.  Both to hep me understand how markets and trading work,
but also seeing how quickly I could pull something together with limited time and an AI junior dev.
The project focuses on **data ingestion, signal generation, and simplified backtesting** to explore swing trading strategies.

I'm not actively working on this at the moment, but I might come back to this and create a watchlist abstraction to test setups on.

---

## Project Overview

- **Purpose**
  The bot was designed to fetch historical and live market data, store it in a structured database, and generate trading signals based on technical analysis. It supports backtesting strategies and could be extended into live execution.

- **Architecture**
  - **FastAPI backend** for serving data and signals
  - **PostgreSQL database** (via Docker) for storing securities, index constituents, OHLCV candles, and backtest results
  - **SQLModel ORM** for clean data models and migrations
  - **Task modules** for ingestion, backfilling, and computation of indicators
  - **Services** wrapping external libraries (e.g. `yfinance`) for data access
  - **Makefile + Poetry** for dependency management and developer workflows

- **Features Implemented**
  - Tracking historical S&P 500 constituents
  - Fetching OHLCV data with backfill and daily update tasks
  - Computing technical indicators
  - Running backtests with configurable execution and exit strategies
  - Code quality enforcement with `black`, `isort`, and `flake8`

---
## Development Guide

###  Project Setup

> **Note:** Poetry 2.0+ no longer includes the `poetry shell` command by default.

To activate the virtual environment manually, use:

```bash
poetry env activate $(poetry env list --full-path | grep Activated | cut -d' ' -f1)
```

#### To add daily cron to update tickers
```bash
chmod +x scripts/setup_cron.sh
make setup-cron
```

##### To confirm it's added
```bash
crontab -l
```

##### To Remove the cron job
```bash
make remove-cron
```

#### For running server + migrations + requirements
```bash
make start
```

#### Running migrations
```bash
make migrations
```

#### Install requirements
```bash
make requirements
```

#### Starting server
```bash
make main
```

#### Running Code Quality checks
```bash
make check
```

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/docs/#installation) version 2.1 or higher
- Docker (for running the database)
