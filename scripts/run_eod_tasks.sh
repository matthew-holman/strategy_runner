#!/bin/bash
set -e

# --- Configuration ---
REPO_ROOT="/Users/matthewh/git/trading-bot"
LOG_FILE="/var/log/trading_tasks.log"

# --- Validate arguments ---
if [ -z "$1" ]; then
    echo "❌ Missing argument: path to Python executable (expected as first argument)" >> "$LOG_FILE"
    exit 1
fi

PYTHON_EXEC="$1"
TASK_SCRIPT="$REPO_ROOT/app/workflows/eod_tasks.py"

# --- Sanity check ---
if [ ! -x "$PYTHON_EXEC" ]; then
    echo "❌ Provided Python executable not found or not executable: $PYTHON_EXEC" >> "$LOG_FILE"
    exit 1
fi

cd "$REPO_ROOT" || exit 1
export PYTHONPATH="$REPO_ROOT"

{
    echo "---- $(date '+%Y-%m-%d %H:%M:%S') Starting EOD tasks ----"
    "$PYTHON_EXEC" "$TASK_SCRIPT"
    echo "---- $(date '+%Y-%m-%d %H:%M:%S') EOD tasks completed ----"
} >> "$LOG_FILE" 2>&1
