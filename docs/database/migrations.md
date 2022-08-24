# Database Migrations

To keep the database structure synchronized with the models defined in the code, Django uses files called migrations
to make changes to the database. Migrations can be applied to bring your database up to date with the current state of
the code, or rolled back to return to a previous state in the database's evolution. Each Django app has
an ordered list of migrations which reflects the progression of its models.

To view the list of migrations in the project, run:

```shell
python manage.py showmigrations
```

## Troubleshooting Migration Issues

If an error occurs during a migration, your database may end up in an in-between or conflicting state.
If this occurs, follow the steps below to repair your database.

Please note that while you're encouraged to fix errors in migration files that you've introduced,
it's not good practice to go into the history and edit past migrations. If necessary, this should only be done with
agreement from the team, and in a manner that does not cause the database structure to diverge on different developers'
machines.

!!! important
    The solutions below may cause you to lose data related to the migration that failed. For example, if your failing
    migration added a field `date_of_birth`, reverting and re-migrating will cause you to lose any values entered in
    this field. If you're worried about loss of data, make a database backup and proceed with caution.

### 1. Recovering from a simple error

In most cases, reverting to the previous migration will be sufficient to solve the issue. Let's say the error occurred
in the patients app, in migration 0003. Execute the following command to restore your database
to the previous migration:

```shell
python manage.py migrate patients 0002
```

!!! note
    You don't have to enter the entire name of the file corresponding to a migration, just the number (e.g. 0002).

Fix the error in your migration file (which caused the initial problem), then apply it again:

```shell
python manage.py migrate patients 0003
```

If both operations complete without errors, your database has been fixed.

### 2. Recovering from an inconsistent state

In rarer cases, a migration interrupted by a failure may leave the database and Django in an inconsistent state.
In these cases, you might have a column that exists in your database, but that Django doesn't think exists,
or vice-versa.

??? question "Why does this happen?"
    MySQL databases don't support transactions for schema alterations, which means that a failure midway through
    will not be rolled back. This is why it's possible to end up with a partially completed migration.

    Source: https://docs.djangoproject.com/en/dev/topics/migrations/#mysql

To recover from such a failure, you'll need direct database access. Use a database client to connect to the `backend-db`
used by Django (check the Docker container for the right port to use), or spin up an instance of adminer in Docker
to connect to the database.

??? note "HeidiSQL Database Client"
    [HeidiSQL](https://www.heidisql.com/) is a free and easy-to-use database client that you can use to connect
    to your database. Install and launch the software, then enter the following values to start a session:
        ```
        - Network type: MariaDB or MySQL (TCP/IP)
        - Hostname / IP: 127.0.0.1
        - User: DATABASE_USER from .env
        - Password: DATABASE_PASSWORD from .env
        - Port: DATABASE_PORT from .env
        ```

Run the following command in the project to print the SQL statements used during your failed database migration
(in this example, we assume migration 0003 failed in the patients app).

```shell
python manage.py sqlmigrate patients 0003
```

What prints as a result of this command will guide you in finding the right element(s) (table, column, etc.) created
during the failed migration. Using your database client, manually undo any changes made by the incomplete
migration. For example, if the migration was supposed to add two columns, but only successfully added one of them,
drop this column. The goal is to scrub away any traces of the migration from your database, as if it had never run.

Once all traces of the migration are gone, fix the errors in your migration file (if any),
and apply the migration again. It should be able to complete fully now that there's nothing left in the database to
conflict with it.

#### migrate --fake

Another tool in your toolbox for recovering from migration failures is the `migrate --fake` command.
This command will mark a migration as done only on paper (putting a checkbox in `showmigrations`), but without
actually running any changes in the database.

If you use this command, it's your responsibility to modify the database directly to make sure it matches the
state described by the migrations marked as done in `showmigrations`.

Example: let's say that migration 0002 added one new table to the database. You previously used
a database client to connect to the DB, and dropped that table. However, when you run `showmigrations`,
it still shows that 0002 was applied (i.e. the table should exist).
At this point, you should run `python manage.py migrate --fake patients 0001`.
This will remove the checkbox for the 0002 migration, correctly expressing that its changes are not currently present
in the database.

!!! important
    Be careful when using the `--fake` flag, since it's easy to lose track of what changes you have to do manually
    to make sure the database state and `showmigrations` match each other. Only use this flag if you know
    what you're doing, or are working in an easily recreated test environment.
