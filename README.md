# Stock Picker bot

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
