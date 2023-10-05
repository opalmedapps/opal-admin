from http import HTTPStatus
from typing import Tuple

from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict
from django.test import Client, RequestFactory
from django.urls.base import reverse

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects, assertTemplateUsed

from opal.users.models import User

from .. import factories
from ..forms import InstitutionForm
from ..models import Institution, Site
from ..views import InstitutionListView, SiteListView

pytestmark = pytest.mark.django_db


# INDEX PAGE

# tuple with general hospital-settings templates and corresponding url names
test_url_template_data: list[Tuple] = [
    (reverse('hospital-settings:index'), 'hospital_settings/index.html'),
    (reverse('hospital-settings:institution-list'), 'hospital_settings/institution/institution_list.html'),
    (reverse('hospital-settings:institution-create'), 'hospital_settings/institution/institution_form.html'),
    (reverse('hospital-settings:site-list'), 'hospital_settings/site/site_list.html'),
    (reverse('hospital-settings:site-create'), 'hospital_settings/site/site_form.html'),
]


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_hospital_settings_urls_exist(admin_client: Client, url: str, template: str) -> None:
    """Ensure that a page exists at desired URL address."""
    response = admin_client.get(url)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_views_use_correct_template(admin_client: Client, url: str, template: str) -> None:
    """Ensure that a page uses appropriate templates."""
    response = admin_client.get(url)

    assertTemplateUsed(response, template)


# INSTITUTION

# tuple with `Institution` templates and corresponding url names
test_institution_url_template_data: list[Tuple] = [
    ('hospital-settings:institution-update', 'hospital_settings/institution/institution_form.html'),
    ('hospital-settings:institution-delete', 'hospital_settings/institution/institution_confirm_delete.html'),
]


@pytest.mark.parametrize(('url_name', 'template'), test_institution_url_template_data)
def test_institution_urls_exist(
    client: Client,
    institution_user: User,
    url_name: str,
    template: str,
) -> None:
    """Ensure that `Institution` pages exists at desired URL address."""
    institution = factories.Institution()
    url = reverse(url_name, args=(institution.id,))
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url_name', 'template'), test_institution_url_template_data)
def test_institution_urls_use_correct_template(
    client: Client,
    institution_user: User,
    url_name: str,
    template: str,
) -> None:
    """Ensure that `Institution` pages exists at desired URL address."""
    institution = factories.Institution()
    url = reverse(url_name, args=(institution.id,))
    response = client.get(url)

    assertTemplateUsed(response, template)


def test_institution_list_displays_all(client: Client, institution_user: User) -> None:
    """Ensure that the institution list page template displays all the institutions."""
    factories.Institution(name='INS1')
    factories.Institution(name='INS2')
    factories.Institution(name='INS3')

    url = reverse('hospital-settings:institution-list')
    response = client.get(url)

    # determine how many institutions are displayed
    soup = BeautifulSoup(response.content, 'html.parser')
    returned_institutions = soup.find('tbody').find_all('tr')
    assert len(returned_institutions) == Institution.objects.count()


def test_institution_list_create_shown(client: Client, institution_user: User) -> None:
    """Ensure that the institution list page displays the create button when there are no institutions."""
    url = reverse('hospital-settings:institution-list')

    response = client.get(url)

    soup = BeautifulSoup(response.content, 'html.parser')
    create_link = soup.find('a', attrs={'href': reverse('hospital-settings:institution-create')})
    assert create_link is not None


def test_institution_list_create_not_shown(user_client: Client) -> None:
    """Ensure that the institution list page does not display the create button when there is an institution."""
    factories.Institution()
    url = reverse('hospital-settings:institution-list')

    response = user_client.get(url)

    soup = BeautifulSoup(response.content, 'html.parser')
    create_link = soup.find('a', attrs={'href': reverse('hospital-settings:institution-create')})
    assert create_link is None


def test_institution_update_object_displayed(client: Client, institution_user: User) -> None:
    """Ensure that the institution detail page displays all fields."""
    institution = factories.Institution(name='TEST1_EN', name_fr='TEST1_FR')

    url = reverse('hospital-settings:institution-update', args=(institution.id,))
    response = client.get(url)

    assertContains(response, 'TEST1_EN')
    assertContains(response, 'TEST1_FR')
    assertContains(response, 'TEST1')


# SITE

# tuple with `Site` templates and corresponding url names
test_site_url_template_data: list[Tuple] = [
    ('hospital-settings:site-update', 'hospital_settings/site/site_form.html'),
    ('hospital-settings:site-delete', 'hospital_settings/site/site_confirm_delete.html'),
]


@pytest.mark.parametrize(('url_name', 'template'), test_site_url_template_data)
def test_site_urls_exist(
    site_user: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that `Site` pages exist at desired URL address."""
    site = factories.Site()
    url = reverse(url_name, args=(site.id,))
    response = site_user.get(url)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url_name', 'template'), test_site_url_template_data)
def test_site_urls_use_correct_template(
    site_user: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that `Site` pages uses appropriate templates."""
    site = factories.Site()
    url = reverse(url_name, args=(site.id,))
    response = site_user.get(url)
    assertTemplateUsed(response, template)


def test_list_all_sites(site_user: Client) -> None:
    """Ensure that the site list page template displays all the institutions."""
    factories.Site(name='ST1')
    factories.Site(name='ST2')
    factories.Site(name='ST3')

    url = reverse('hospital-settings:site-list')
    response = site_user.get(url)

    # determine how many sites are displayed
    soup = BeautifulSoup(response.content, 'html.parser')
    returned_sites = soup.find('tbody').find_all('tr')
    assert len(returned_sites) == Site.objects.count()


def test_site_update_object_displayed(site_user: Client) -> None:
    """Ensure that the site detail page displays all the fields."""
    site = factories.Site(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        longitude=13.381969928741455,
        latitude=52.50479381812203,
    )

    url = reverse('hospital-settings:site-update', args=(site.id,))
    response = site_user.get(url)

    assertContains(response, 'TEST1_EN')
    assertContains(response, 'TEST1_FR')
    assertContains(response, 'http://127.0.0.1:8000/hospital-settings/site/1/fr')
    assertContains(response, 'http://127.0.0.1:8000/hospital-settings/site/1/en')
    assertContains(response, 'TEST1')
    assertContains(response, site.institution.name)


def test_institution_created(client: Client, institution_user: User, institution_form: InstitutionForm) -> None:
    """Ensure that an institution can be successfully created."""
    url = reverse('hospital-settings:institution-create')

    assert institution_form.is_valid()

    client.post(url, data=institution_form.cleaned_data, files=institution_form.files)

    assert Institution.objects.count() == 1
    assert Institution.objects.all()[0].name == institution_form.cleaned_data['name_en']


def test_incomplete_institution_create(
    client: Client,
    institution_user: User,
    incomplete_institution_form: InstitutionForm,
) -> None:
    """Ensure that new incomplete institution (with missing institution code) form cannot be posted to the server."""
    url = reverse('hospital-settings:institution-create')

    response = client.post(
        url,
        data=incomplete_institution_form.data,
        files=incomplete_institution_form.files,
    )

    assertContains(response=response, text='This field is required.', status_code=HTTPStatus.OK)
    assert Institution.objects.count() == 0


def test_institution_with_no_logos_create(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that new incomplete institution (with missing logo images) form cannot be posted to the server."""
    url = reverse('hospital-settings:institution-create')
    form_data = dict(institution_form.data)

    form_data.pop('logo_fr')
    form_data.pop('logo_en')

    response = client.post(
        url,
        data=form_data,
    )

    assertContains(response=response, text='This field is required.', status_code=HTTPStatus.OK)
    assert Institution.objects.count() == 0


def test_institution_with_no_terms_of_use_create(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that new incomplete institution (with missing terms of use file) form cannot be posted to the server."""
    url = reverse('hospital-settings:institution-create')
    form_data = dict(institution_form.data)
    form_data.pop('terms_of_use_fr')
    form_data.pop('terms_of_use_en')

    response = client.post(
        url,
        data=form_data,
    )

    assertContains(response=response, text='This field is required.', status_code=HTTPStatus.OK)
    assert Institution.objects.count() == 0


def test_institution_with_no_adulthood_age_create(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that new incomplete institution (with missing adulthood age) form cannot be posted to the server."""
    url = reverse('hospital-settings:institution-create')
    form_data = dict(institution_form.data)
    form_data.pop('adulthood_age')

    response = client.post(
        url,
        data=form_data,
    )

    assertContains(response=response, text='This field is required.', status_code=HTTPStatus.OK)
    assert Institution.objects.count() == 0


def test_institution_with_no_labs_non_interpretable_create(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that the institution (with missing non interpretable labs) form cannot be posted to the server."""
    url = reverse('hospital-settings:institution-create')
    form_data = dict(institution_form.data)
    form_data.pop('non_interpretable_lab_result_delay')

    response = client.post(
        url,
        data=form_data,
    )

    assertContains(response=response, text='This field is required.', status_code=HTTPStatus.OK)
    assert Institution.objects.count() == 0


def test_institution_with_no_labs_interpretable_create(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that the institution (with missing interpretable labs) form cannot be posted to the server."""
    url = reverse('hospital-settings:institution-create')
    form_data = dict(institution_form.data)
    form_data.pop('interpretable_lab_result_delay')

    response = client.post(
        url,
        data=form_data,
    )

    assertContains(response=response, text='This field is required.', status_code=HTTPStatus.OK)
    assert Institution.objects.count() == 0


def test_institution_successful_create_redirects(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that after a successful creation of an institution, the page is redirected to the list page."""
    url = reverse('hospital-settings:institution-create')
    assert institution_form.is_valid()
    response = client.post(url, data=institution_form.cleaned_data, files=institution_form.files)

    assertRedirects(response, reverse('hospital-settings:institution-list'))


def test_institution_updated(client: Client, institution_user: User, institution_form: InstitutionForm) -> None:
    """Ensure that an institution can be successfully updated."""
    assert institution_form.is_valid()

    institution_form.save()

    form_data = dict(institution_form.data)
    form_data['name_en'] = 'updated name_en'
    form_data['name_fr'] = 'updated name_fr'

    url = reverse('hospital-settings:institution-update', args=(institution_form.instance.id,))
    client.post(path=url, data=form_data, files=institution_form.files)

    assert Institution.objects.all()[0].name_en == 'updated name_en'  # type: ignore[attr-defined]
    assert Institution.objects.all()[0].name_fr == 'updated name_fr'  # type: ignore[attr-defined]


def test_incomplete_institution_update(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that incomplete institution (with missing institution code) form cannot update an existing institution."""
    assert institution_form.is_valid()
    institution_form.save()

    url = reverse('hospital-settings:institution-update', args=(institution_form.instance.id,))
    form_data = dict(institution_form.data)
    form_data['name_en'] = 'updated name_en'
    form_data['name_fr'] = 'updated name_fr'
    form_data.pop('code')

    response = client.post(
        url,
        data=form_data,
        files=institution_form.files,
    )

    assertContains(response=response, text='This field is required.', status_code=HTTPStatus.OK)
    assert Institution.objects.all()[0].name_en != 'updated name_en'  # type: ignore[attr-defined]
    assert Institution.objects.all()[0].name_fr != 'updated name_fr'  # type: ignore[attr-defined]


def test_institution_with_no_logos_update(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that institution form (with missing logo images) can update an existing institution."""
    assert institution_form.is_valid()
    institution_form.save()

    url = reverse('hospital-settings:institution-update', args=(institution_form.instance.id,))
    form_data = dict(institution_form.data)
    form_data['name_en'] = 'updated name_en'
    form_data['name_fr'] = 'updated name_fr'
    form_data.pop('logo_fr')
    form_data.pop('logo_en')

    response = client.post(
        url,
        data=form_data,
    )

    assertRedirects(response, reverse('hospital-settings:institution-list'))
    assert Institution.objects.all()[0].name_en == 'updated name_en'  # type: ignore[attr-defined]
    assert Institution.objects.all()[0].name_fr == 'updated name_fr'  # type: ignore[attr-defined]


def test_institution_with_no_terms_of_use_update(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that institution form (with missing terms of use file) can update an existing institution."""
    assert institution_form.is_valid()
    institution_form.save()

    url = reverse('hospital-settings:institution-update', args=(institution_form.instance.id,))
    form_data = dict(institution_form.data)
    form_data['name_en'] = 'updated name_en'
    form_data['name_fr'] = 'updated name_fr'
    form_data.pop('terms_of_use_fr')
    form_data.pop('terms_of_use_en')

    response = client.post(
        url,
        data=form_data,
    )

    assertRedirects(response, reverse('hospital-settings:institution-list'))
    assert Institution.objects.all()[0].name_en == 'updated name_en'  # type: ignore[attr-defined]
    assert Institution.objects.all()[0].name_fr == 'updated name_fr'  # type: ignore[attr-defined]


def test_institution_with_no_adulthood_age_update(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that incomplete institution (with missing adulthood age) form cannot update an existing institution."""
    assert institution_form.is_valid()
    institution_form.save()

    url = reverse('hospital-settings:institution-update', args=(institution_form.instance.id,))
    form_data = dict(institution_form.data)
    form_data['name_en'] = 'updated name_en'
    form_data['name_fr'] = 'updated name_fr'
    form_data.pop('adulthood_age')

    response = client.post(
        url,
        data=form_data,
    )

    assertContains(response=response, text='This field is required.', status_code=HTTPStatus.OK)
    assert Institution.objects.all()[0].name_en != 'updated name_en'  # type: ignore[attr-defined]
    assert Institution.objects.all()[0].name_fr != 'updated name_fr'  # type: ignore[attr-defined]


def test_institution_with_no_labs_non_interpretable_update(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that institution (with missing non interpretable labs) form cannot update an existing institution."""
    assert institution_form.is_valid()
    institution_form.save()

    url = reverse('hospital-settings:institution-update', args=(institution_form.instance.id,))
    form_data = dict(institution_form.data)
    form_data['name_en'] = 'updated name_en'
    form_data['name_fr'] = 'updated name_fr'
    form_data.pop('non_interpretable_lab_result_delay')

    response = client.post(
        url,
        data=form_data,
    )

    assertContains(response=response, text='This field is required.', status_code=HTTPStatus.OK)
    assert Institution.objects.all()[0].name_en != 'updated name_en'  # type: ignore[attr-defined]
    assert Institution.objects.all()[0].name_fr != 'updated name_fr'  # type: ignore[attr-defined]


def test_institution_with_no_labs_interpretable_update(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that institution (with missing interpretable labs) form cannot update an existing institution."""
    assert institution_form.is_valid()
    institution_form.save()

    url = reverse('hospital-settings:institution-update', args=(institution_form.instance.id,))
    form_data = dict(institution_form.data)
    form_data['name_en'] = 'updated name_en'
    form_data['name_fr'] = 'updated name_fr'
    form_data.pop('interpretable_lab_result_delay')

    response = client.post(
        url,
        data=form_data,
    )

    assertContains(response=response, text='This field is required.', status_code=HTTPStatus.OK)
    assert Institution.objects.all()[0].name_en != 'updated name_en'  # type: ignore[attr-defined]
    assert Institution.objects.all()[0].name_fr != 'updated name_fr'  # type: ignore[attr-defined]


def test_institution_successful_update_redirects(
    client: Client,
    institution_user: User,
    institution_form: InstitutionForm,
) -> None:
    """Ensure that after a successful update of an institution, the page is redirected to the list page."""
    assert institution_form.is_valid()
    institution_form.save()
    url = reverse('hospital-settings:institution-update', args=(institution_form.instance.id,))

    form_data = dict(institution_form.data)
    form_data['name_en'] = 'updated name_en'
    form_data['name_fr'] = 'updated name_fr'

    response = client.post(url, data=form_data, files=institution_form.files)

    assertRedirects(response, reverse('hospital-settings:institution-list'))


def test_institution_successful_delete_redirects(client: Client, institution_user: User) -> None:
    """Ensure that after a successful delete of an institution, the page is redirected to the list page."""
    institution = factories.Institution()
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    response = client.delete(url)

    assertRedirects(response, reverse('hospital-settings:institution-list'))


def test_institution_deleted(client: Client, institution_user: User) -> None:
    """Ensure that an institution is deleted from the database."""
    institution = factories.Institution()
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    client.delete(url)

    assert Institution.objects.count() == 0


def test_site_created(site_user: Client) -> None:
    """Ensure that a site can be successfully created."""
    institution = factories.Institution()
    url = reverse('hospital-settings:site-create')
    site = factories.Site.build(institution=institution)
    form_data = model_to_dict(site, exclude=['id'])

    site_user.post(url, data=form_data)

    assert Site.objects.count() == 1
    assert Site.objects.all()[0].name == site.name


def test_site_successful_create_redirects(site_user: Client) -> None:
    """Ensure that after a successful creation of a site, the page is redirected to the list page."""
    institution = factories.Institution()
    url = reverse('hospital-settings:site-create')
    site = factories.Site.build(institution=institution)
    form_data = model_to_dict(site, exclude=['id'])

    response = site_user.post(url, data=form_data)

    assertRedirects(response, reverse('hospital-settings:site-list'))


def test_site_updated(site_user: Client) -> None:
    """Ensure that a site can be successfully updated."""
    site = factories.Site()

    url = reverse('hospital-settings:site-update', args=(site.id,))
    site.name = 'updated'
    form_data = model_to_dict(site)
    site_user.post(url, data=form_data)

    assert Site.objects.all()[0].name == 'updated'


def test_site_successful_update_redirects(
    site_user: Client,
) -> None:
    """Ensure that after a successful update of a site, the page is redirected to the list page."""
    site = factories.Site()
    url = reverse('hospital-settings:site-update', args=(site.id,))
    form_data = model_to_dict(site)

    response = site_user.post(url, data=form_data)

    assertRedirects(response, reverse('hospital-settings:site-list'))


def test_site_successful_delete_redirects(site_user: Client) -> None:
    """Ensure that after a successful delete of a site, the page is redirected to the list page."""
    site = factories.Site()
    url = reverse('hospital-settings:site-delete', args=(site.id,))

    response = site_user.delete(url)

    assertRedirects(response, reverse('hospital-settings:site-list'))


def test_site_deleted(site_user: Client) -> None:
    """Ensure that a site is deleted from the database."""
    site = factories.Site()
    url = reverse('hospital-settings:site-delete', args=(site.id,))

    site_user.delete(url)

    assert Site.objects.count() == 0


@pytest.mark.parametrize(
    'url_name', [
        reverse('hospital-settings:institution-list'),
        reverse('hospital-settings:institution-update', args=(1,)),
        reverse('hospital-settings:institution-create'),
        reverse('hospital-settings:institution-delete', args=(1,)),
    ],
)
def test_institution_permission_required_fail(user_client: Client, django_user_model: User, url_name: str) -> None:
    """Ensure that `institution` permission denied error is raised when not having privilege."""
    user = django_user_model.objects.create(username='test_institution_user')
    user_client.force_login(user)
    factories.Institution(pk=1)
    response = user_client.get(url_name)
    request = RequestFactory().get(response)  # type: ignore[arg-type]
    request.user = user

    with pytest.raises(PermissionDenied):
        InstitutionListView.as_view()(request)


@pytest.mark.parametrize(
    'url_name', [
        reverse('hospital-settings:institution-list'),
        reverse('hospital-settings:institution-update', args=(1,)),
        reverse('hospital-settings:institution-create'),
        reverse('hospital-settings:institution-delete', args=(1,)),
    ],
)
def test_institution_permission_required_success(user_client: Client, django_user_model: User, url_name: str) -> None:
    """Ensure that `institution` can be accessed with the required permission."""
    user = django_user_model.objects.create(username='test_institution_user')
    user_client.force_login(user)
    permission = Permission.objects.get(codename='can_manage_institutions')
    user.user_permissions.add(permission)
    factories.Institution(pk=1)

    response = user_client.get(url_name)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.xfail(condition=True, reason='the sidebar menus are removed', strict=True)
def test_institution_response_contains_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that institution menu is displayed for users with permission."""
    user = django_user_model.objects.create(username='test_institution_user')
    user_client.force_login(user)
    permission = Permission.objects.get(codename='can_manage_institutions')
    user.user_permissions.add(permission)

    response = user_client.get(reverse('hospital-settings:index'))

    assertContains(response, 'Institutions')


def test_institution_response_no_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that institution menu is not displayed for users without permission."""
    user = django_user_model.objects.create(username='test_institution_user')
    user_client.force_login(user)

    response = user_client.get(reverse('hospital-settings:index'))

    assertNotContains(response, 'Institutions')


@pytest.mark.parametrize(
    'url_name', [
        reverse('hospital-settings:site-list'),
        reverse('hospital-settings:site-update', args=(1,)),
        reverse('hospital-settings:site-create'),
        reverse('hospital-settings:site-delete', args=(1,)),
    ],
)
def test_site_permission_required_fail(user_client: Client, django_user_model: User, url_name: str) -> None:
    """Ensure that `site` permission denied error is raised when not having privilege."""
    user = django_user_model.objects.create(username='test_site_user')
    user_client.force_login(user)
    factories.Site(pk=1)
    response = user_client.get(url_name)
    request = RequestFactory().get(response)  # type: ignore[arg-type]
    request.user = user

    with pytest.raises(PermissionDenied):
        SiteListView.as_view()(request)


@pytest.mark.parametrize(
    'url_name', [
        reverse('hospital-settings:site-list'),
        reverse('hospital-settings:site-update', args=(1,)),
        reverse('hospital-settings:site-create'),
        reverse('hospital-settings:site-delete', args=(1,)),
    ],
)
def test_site_permission_required_success(user_client: Client, django_user_model: User, url_name: str) -> None:
    """Ensure that `site` can be accessed with the required permission."""
    user = django_user_model.objects.create(username='test_site_user')
    user_client.force_login(user)
    permission = Permission.objects.get(codename='can_manage_sites')
    user.user_permissions.add(permission)
    factories.Site(pk=1)

    response = user_client.get(url_name)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.xfail(condition=True, reason='the sidebar menus are removed', strict=True)
def test_site_response_contains_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that site menu is displayed for users with permission."""
    user = django_user_model.objects.create(username='test_site_user')
    user_client.force_login(user)
    permission = Permission.objects.get(codename='can_manage_sites')
    user.user_permissions.add(permission)

    response = user_client.get(reverse('hospital-settings:index'))

    assertContains(response, 'Sites')


def test_site_response_no_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that site menu is not displayed for users without permission."""
    user = django_user_model.objects.create(username='test_site_user')
    user_client.force_login(user)

    response = user_client.get(reverse('hospital-settings:index'))

    assertNotContains(response, 'Sites')


def test_institution_site_response_no_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that hospital settings menu is not displayed for users without institution and site permissions."""
    user = django_user_model.objects.create(username='test_site_user')
    user_client.force_login(user)

    response = user_client.get(reverse('hospital-settings:index'))

    soup = BeautifulSoup(response.content, 'html.parser')
    menu_group = soup.find_all(
        'button',
        attrs={'class': 'btn-toggle'},
        string=lambda value: 'Hospital Settings' in value,
    )

    assert not menu_group
