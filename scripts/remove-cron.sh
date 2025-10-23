# scripts/remove_cron.sh
#!/bin/bash

SCRIPT_NAME="run_eod_tasks.sh"
crontab -l | grep -v "$SCRIPT_NAME" | crontab -
echo "🧹 Cron job(s) related to $SCRIPT_NAME removed."
