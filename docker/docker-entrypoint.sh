#!/bin/sh
set -euxo pipefail

# Start the cron scheduler service
service cron start

# Add new cron job to the cron tab
crontab /etc/cron.d/check-databases-deviations-cron

# execute remaining commands/arguments
exec "$@"
