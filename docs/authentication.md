# Authentication

The default permissions policy is defined in [CustomDjangoModelPermissions][opal.utils.drf_permissions.CustomDjangoModelPermissions]. It restricts accesses to at least require the `view` model permissions (for `GET` requests).

For more information see the [DRF documentation on permissions](https://www.django-rest-framework.org/api-guide/permissions/#permissions).

## Technical Users

This project is set up with the support for authentication tokens. Follow these steps to provide access to a non-human user:

1. Create a user without a password
    1. `python manage.py shell_plus`
    2. `User.objects.create(username='nonhumanusername')`
2. Log into the admin site
3. Set permissions
    a. assign permissions directly to user, or
    b. assign user to a group which has the permissions
4. Create auth token for this user via the admin site

Now, requests can be made with this user by providing the following header in requests:

```shell
Authorization: Token <insert_token_key>
```

For example, using `curl` a request could be made as follows:

```shell
curl -H 'Authorization: Token <insert_token_key>' http://localhost:8000/api/sites
```
