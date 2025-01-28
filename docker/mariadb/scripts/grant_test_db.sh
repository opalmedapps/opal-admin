#!/bin/bash

# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -Eeuo pipefail

# grant user to create test databases
# backticks need to be escaped to make this work
MYSQL_PWD=$MARIADB_ROOT_PASSWORD mysql -uroot -hlocalhost -e "GRANT ALL PRIVILEGES ON \`test_${MARIADB_DATABASE}%\`.* TO \`$MARIADB_USER\`@\`%\`;"
