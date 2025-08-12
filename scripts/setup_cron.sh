#!/bin/bash

# Resolve the script directory (repo root assumed to be one level up from scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Determine VENV python path (assumes script is being run from an activated venv)
if [ -n "$VIRTUAL_ENV" ]; then
    PYTHON_EXEC="$VIRTUAL_ENV/bin/python"
else
    echo "This script should be run from within an activated virtual environment."
    exit 1
fi

# Resolve the eod_tasks.py script path
TASK_SCRIPT="$REPO_ROOT/daily_tasks.py"  # adjust if location differs

# Ensure the log directory exists
LOG_FILE="/var/log/trading_tasks.log"
sudo touch "$LOG_FILE"
sudo chown "$(whoami)" "$LOG_FILE"

# Define the cron job
CRON_JOB="0 6 * * * $PYTHON_EXEC $TASK_SCRIPT >> $LOG_FILE 2>&1"

# Check if the job already exists
if crontab -l 2>/dev/null | grep -F "$TASK_SCRIPT" >/dev/null; then
    echo "✅ Cron job already exists. Skipping..."
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added:"
    echo "$CRON_JOB"
fi
