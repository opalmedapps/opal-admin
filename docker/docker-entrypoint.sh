#!/bin/sh
# option pipefail available on alpine sh
# shellcheck disable=SC3040
set -euo pipefail

# Start the cron scheduler service and log to the container's stdout
busybox crond -b -l 8 -L /dev/stdout

# execute remaining commands/arguments
exec "$@"
