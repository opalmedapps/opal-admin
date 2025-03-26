# Authentication

The default permissions policy is defined in [CustomDjangoModelPermissions][opal.core.drf_permissions.CustomDjangoModelPermissions]. It restricts accesses to at least require the `view` model permissions (for `GET` requests).

For more information see the [DRF documentation on permissions](https://www.django-rest-framework.org/api-guide/permissions/#permissions).

## Technical Users

This project is set up with the support for authentication tokens. Follow these steps to provide access to a non-human user:

1. Create a user without a password

    ```sh
    python manage.py shell_plus
    User.objects.create(username='nonhumanusername')
    ```

2. Log into the Django admin site
3. Set permissions by assigning them directly to the user or to a group the user is a part of

    For example: To allow the user to view institutions of the `hospital_settings` app, choose the permission `hospital_settings | institution | Can view institution`.

4. Create auth token for this user via the Django admin site

Now, requests can be made with this user by providing the following header in requests:

```shell
Authorization: Token <insert_token_key>
```

For example, using `curl` a request could be made as follows:

```shell
curl -H 'Authorization: Token <insert_token_key>' http://localhost:8000/api/sites
```
