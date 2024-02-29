#!/bin/bash
# Test management commands referenced in the crontab
set -euo pipefail

contents=$(cat docker/crontab | grep "manage.py")

while read -r line;
do
    text="${line#*manage.py }"
    command="${text%% >*}"
    echo "found command '$command', executing 'python manage.py $command'..."
    python manage.py "$command"
done <<< "$contents"
