#!/bin/sh
# option pipefail available on alpine sh
# shellcheck disable=SC3040
set -euo pipefail

# Start the cron scheduler service
# service cron start

# execute remaining commands/arguments
exec "$@"
