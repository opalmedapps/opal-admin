# Standard and Custom Permissions in Django

This section explains the user permissions management and the convention of adding new permissions. The design and structure of such convention are inspired by standard Django project documentation.


For more information see the [Django Documentation on permissions and authorization](https://docs.djangoproject.com/en/dev/topics/auth/default/#permissions-and-authorization).

When it comes to permissions, the simplest form of adding a new permission is to use the Django standard admin panel and the standard models permissions. However, there are more complicated scenarios such as:

1. front-end permissions at HTML component level.

2. model view permissions, but no editing or changing.

3. user-specific permissions other than standard `is_staff`.

4. group-specific permissions where only certain group of users are allowed to access/use certain features of the system.


Django admin panel provides nice ready-to-use GUI to manage those permissions, it allows adding permissions to specific users. In addition, it allows forming new groups and assign permissions to them. However, it does not provide a way to add custom permissions. In this documentation, custom permissions are explained.

## Adding Custom Permissions

### Introducing custom permission to a model
In order to add permissions, and allow its use in the Django Admin Site, follow this guide:

1. Add permission to Meta information of the model. This example is applied on the `Site` model in the `hospital_settings` app
```python
class Meta:
        permissions = (('new_perm','New Custom Permission'),)
        ordering = ['name']
        verbose_name = _('Site')
        verbose_name_plural = _('Sites')
```

2. Run
   ```python
   python manage.py makemigrations
   python manage.py migrate
   ```

3. Go to http://localhost:8000/admin or project-link/admin --> users --> select certain user --> scroll down to see all permissions

???+ note

    a. `permissions = (('new_perm','New Custom Permission'),)`
            the first argument is called codename, the second argument is called name. 
    
    b. In order to know what is the codename of a permission(s) for a specific model run the following command after running
            `python manage.py shell_plus`
    ```python
     for perm in Permission.objects.filter(content_type=ContentType.objects.get_for_model(Site)):
        print(perm.codename)
    ```

### Restricting access of model templates in views

By now there should be a new permission available to be used. To restrict the access to the view to only those who have this new permission follow this guide:

1. Import [`PermissionRequiredMixin`](https://docs.djangoproject.com/en/dev/topics/auth/default/#the-permissionrequiredmixin-mixin) Django package.
```python
from django.contrib.auth.mixins import PermissionRequiredMixin
```

2. Pass it to the view. Considering the site example for the same model considered above.
```python
     class SiteListView(PermissionRequiredMixin, SingleTableView):
         model = Site
         # use app_name.codename of the permission
         required_permissions=('hospital_settings.new_perm',)
         table_class = tables.SiteTable
         template_name = 'hospital_settings/site/site_list.html'
```

### Applying certain restrictions on front-end at using template tags

Use the template tag [`{{ perms }}`](https://docs.djangoproject.com/en/dev/topics/auth/default/#permissions) in the HTML template for further restrictions:
```html
{% if perms.hospital_settings.new_perm %}
    <!-- Do Something -->
{% endif %}
```

???+ note

      `{{ perms }}` can be used in the HTML templates without adding `PermissionRequiredMixin`.

## Testing the permissions

The [`PermissionDenied`](https://docs.djangoproject.com/en/dev/topics/testing/tools/#exceptions) exception is raised when a user does not have the required permission to access a view. This applies to all permissions, whether built-in or custom. Hence, we can use it to test if this exception is raised. In the references below, there is more than one suggestion to test. However, the most compact and straight forward way to test is the following: In the `test_views.py` file add the following:

```python
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.urls import reverse
from django.contrib.auth.models import Permission

    # FAIL CASE: to raise permission denied permission when user does not have right privilege 
    def test_site_permission_required_fail(user_client: Client, django_user_model: User) -> None:
       """Ensure that `site` permission denied error is raised when not having privilege"""
       user = django_user_model.objects.create(username='test_site_user')
       user_client.force_login(user)
       response = user_client.get(reverse('hospital-settings:site-list'))
       request = RequestFactory().get(response)
       request.user = user
   
       with pytest.raises(PermissionDenied):
           SiteListView.as_view()(request)
           
    # PASS CASE: to not raise permission denied permission when user has right privilege 
    def test_site_permission_required_success(user_client: Client, django_user_model: User) -> None:
       """Ensure that `site` cannot be accessed without the required permission."""
       user = django_user_model.objects.create(username='test_site_user')
       user_client.force_login(user)
       permission = Permission.objects.get(codename='new_perm')
       user.user_permissions.add(permission)
       response = user_client.get(reverse('hospital-settings:site-list'))
       request = RequestFactory().get(response)
       request.user = user
       SiteListView.as_view()(request)

```

### References

1. [How To Test - PermissionRequiredMixin]( https://splunktool.com/test-permissionrequiredmixin-raises-permissiondenied-instead-of-403)
2. [How To raise 403 instead of PermissionDenied]( https://stackoverflow.com/questions/42284168/test-permissionrequiredmixin-raises-permissiondenied-instead-of-403)
3. [PermissionDenied Exception](https://docs.djangoproject.com/en/dev/topics/testing/tools/#exceptions)
