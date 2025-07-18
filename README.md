## Development Guide

### 📦 Project Setup

> **Note:** Poetry 2.0+ no longer includes the `poetry shell` command by default.

To activate the virtual environment manually, use:

```bash
poetry env activate $(poetry env list --full-path | grep Activated | cut -d' ' -f1)

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

### add pre commit hook for formatting
pre-commit install
