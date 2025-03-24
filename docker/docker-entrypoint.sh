#!/bin/sh

# SPDX-FileCopyrightText: Copyright (C) 2021 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# option pipefail available on alpine sh
# shellcheck disable=SC3040
set -euo pipefail

# execute remaining commands/arguments
exec "$@"
