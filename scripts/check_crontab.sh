#!/bin/sh
# Test management commands referenced in the crontab
# option pipefail available on alpine sh
# shellcheck disable=SC3040
set -euo pipefail

# get lines that call a management command
contents=$(cat docker/crontab | grep "manage.py")

while read -r line;
do
    # extract command from each line via bash parameter expansion
    # everything after "manage.py "
    command="${line#*manage.py }"
    # everything before the first " >"
    command="${command%% >*}"
    echo "found command '$command', executing 'python manage.py $command --help'..."
    python manage.py "$command" --help
done << EOF
$contents
EOF
