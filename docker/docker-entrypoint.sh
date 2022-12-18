#!/bin/sh

service cron start

# execute remaining commands/arguments
exec "$@"
