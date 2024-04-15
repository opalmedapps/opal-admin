#!/bin/sh
# option pipefail available on alpine sh
# shellcheck disable=SC3040
set -euo pipefail

# Start the cron scheduler service and log to the container's stdout
busybox crond -b -l 7 -L /proc/1/fd/1

# execute remaining commands/arguments
exec "$@"
