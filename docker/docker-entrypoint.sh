#!/bin/sh

# Start the cron scheduler service
service cron start

# execute remaining commands/arguments
exec "$@"
