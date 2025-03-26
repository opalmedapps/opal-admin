#!/bin/sh
# option pipefail available on alpine sh
# shellcheck disable=SC3040
set -euo pipefail

# execute remaining commands/arguments
exec "$@"
