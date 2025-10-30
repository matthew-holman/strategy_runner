#!/bin/bash
set -e

# --- Resolve paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

RUN_SCRIPT="$SCRIPT_DIR/run_eod_tasks.sh"
LOG_FILE="/var/log/trading_tasks.log"

# --- Determine Python executable ---
if [ -n "$VIRTUAL_ENV" ]; then
    PYTHON_EXEC="$VIRTUAL_ENV/bin/python"
else
    echo "❌ This script must be run from within an activated virtual environment."
    exit 1
fi

# --- Ensure log file exists ---
sudo touch "$LOG_FILE"
sudo chown "$(whoami)" "$LOG_FILE"

# --- Define cron job ---
CRON_JOB="0 4 * * * $RUN_SCRIPT $PYTHON_EXEC >> $LOG_FILE 2>&1"

# --- Add if missing ---
if crontab -l 2>/dev/null | grep -F "$RUN_SCRIPT" >/dev/null; then
    echo "✅ Cron job already exists for $RUN_SCRIPT"
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added:"
    echo "$CRON_JOB"
fi
