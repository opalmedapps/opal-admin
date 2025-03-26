#!/bin/bash
set -Eeuo pipefail

# grant user to create test databases
# backticks need to be escaped to make this work
MYSQL_PWD=$MARIADB_ROOT_PASSWORD mysql -uroot -hlocalhost -e "GRANT ALL PRIVILEGES ON \`test_${MARIADB_DATABASE}%\`.* TO \`$MARIADB_USER\`@\`%\`;"
