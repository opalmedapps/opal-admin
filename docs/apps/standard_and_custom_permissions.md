# Standard Django Admin Permissions

This section explains the user permissions management and the convention of adding new permissions. The design and structure of such convention are inspired by standard Django project documentation.


For more information see the [Django Documentation - PermissionRequiredMixin]( https://docs.djangoproject.com/en/4.1/topics/auth/default/#:~:text=The%20PermissionRequiredMixin%20mixin%C2%B6).

When it comes to permissions, the simplest form of adding a new permission is to use the django standard admin panel and the standard models permissions. However, there are more complicated scenarios such as:

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
*NOTES*

1.1 `permissions = (('new_perm','New Custom Permission'),)`
        the first argument is called codename, the second argument is called name. 

1.2 In order to know what is the codename of a permission(s) for a specific model run the following command after running
        `python manage.py shell_plus`
```python
 for perm in Permission.objects.filter(content_type=ContentType.objects.get_for_model(Site))
    print(perm.codename)
```
2. Run
   ```python
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Go to http://localhost:8000/admin or project-link/admin --> users --> select certain user --> scroll down to see all permissions

### Restricting access of model templates in views

By far there should be a new permission available to be used. To restrict the access to the view to only those who have this new permission follow this guide:

1. Import `PermissionRequiredMixin` Django package.

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

Use the template tag `{{ perms }}` in the HTML file for further restrictions:
```html
{% if perms.hospital_settings.new_perm %}
    <!-- Do Something -->
{% endif %}
```
*NOTE* `{{ perms }}` can be used in the HTML templates without adding `PermissionRequiredMixin`.
