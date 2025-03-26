"""Test module for the `users` app REST API viewsets endpoints."""
import secrets
from collections.abc import Callable
from http import HTTPStatus

from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from config.settings.base import USER_MANAGER_GROUP_NAME
from opal.users import factories as user_factories
from opal.users.models import ClinicalStaff, User

pytestmark = pytest.mark.django_db


def test_userviewset_unauthenticated_unauthorized(
    api_client: APIClient,
    user: User,
    user_with_permission: Callable[[str], User],
) -> None:
    """Test that unauthenticated and unauthorized users cannot access the API."""
    url = reverse('api:users-detail', kwargs={'username': 'test'})

    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

    api_client.force_login(user_with_permission('users.view_clinicalstaff'))
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.OK


def test_userviewset_create_user_in_group_no_permission(user_api_client: APIClient) -> None:
    """Test the fail of the creating a new user in a group(s) when user does not have permission."""
    response = user_api_client.post(reverse('api:users-list'))

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.data['detail'] == 'You do not have permission to perform this action.'


def test_userviewset_update_user_in_group_no_permission(user_api_client: APIClient) -> None:
    """Test the fail of the updating a user group(s) when user does not have permission."""
    response = user_api_client.put(reverse('api:users-detail', kwargs={'username': 'foo'}))

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.data['detail'] == 'You do not have permission to perform this action.'


def test_userviewset_retrieve_user_in_group_pass(
    api_client: APIClient,
    user_with_permission: Callable[[str], User],
) -> None:
    """Test the pass of the retrieving user and their group(s)."""
    api_client.force_login(user_with_permission('users.view_clinicalstaff'))
    # add two groups to add a user to one of them
    user_factories.GroupFactory()
    group = user_factories.GroupFactory(name='group')
    # add clinical staff user
    user = user_factories.ClinicalStaff()
    group.user_set.add(user)

    response = api_client.get(reverse(
        'api:users-detail',
        kwargs={'username': user.username},
    ))

    assert response.status_code == HTTPStatus.OK
    assert response.data == {'groups': [group.pk]}
    assert len(response.data['groups']) == 1


def test_userviewset_add_group_update_user_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of the updating a user and add to a group."""
    api_client.force_login(user=admin_user)
    # add two groups
    group1 = user_factories.GroupFactory(name='group1')
    group2 = user_factories.GroupFactory(name='group2')
    # add one user and add it to one group
    user = user_factories.ClinicalStaff(username='test_clinical_user')
    group2.user_set.add(user)

    # test retrieve
    response = api_client.get(reverse(
        'api:users-detail',
        kwargs={'username': user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data == {'groups': [group2.pk]}
    assert len(response.data['groups']) == 1

    # change the groups and the name of the user
    response.data['groups'].append(group1.pk)
    data = {
        'groups': response.data['groups'],
        'username': 'new_clinical_user',
    }
    response_put = api_client.put(
        reverse(
            'api:users-detail',
            kwargs={'username': user.username},
        ),
        data=data,
    )

    # test if retrieve gets all user groups and if the user groups are updated
    assert response_put.status_code == HTTPStatus.OK
    assert len(response_put.data['groups']) == 2
    assert response_put.data == {
        'groups': [group1.pk, group2.pk],
        'username': 'new_clinical_user',
    }
    # assert the user and groups are updated in the database
    clinical_user = ClinicalStaff.objects.get(pk=user.pk)
    assert clinical_user.username == 'new_clinical_user'
    assert clinical_user.groups.count() == 2


def test_userviewset_add_multiple_groups_to_user_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of editing a user and add to multiple groups."""
    api_client.force_login(user=admin_user)
    group1 = user_factories.GroupFactory(name='group1')
    group2 = user_factories.GroupFactory(name='group2')
    group3 = user_factories.GroupFactory(name='group3')

    # add one user and add it to one group
    user = user_factories.ClinicalStaff()
    group2.user_set.add(user)

    # test retrieve
    response = api_client.get(reverse(
        'api:users-detail',
        kwargs={'username': user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data == {'groups': [group2.pk]}
    assert len(response.data['groups']) == 1

    # change the groups of the user by adding one more group
    response.data['groups'].append(group1.pk)
    response.data['groups'].append(group3.pk)

    data = {
        'groups': response.data['groups'],
        'username': 'new_clinical_user',
    }
    response_put = api_client.put(
        reverse(
            'api:users-detail',
            kwargs={'username': user.username},
        ),
        data=data,
    )
    # test if retrieve gets all user groups and if the user groups are updated
    assert response_put.status_code == HTTPStatus.OK
    assert len(response_put.data['groups']) == 3
    assert response_put.data == {
        'groups': [group1.pk, group2.pk, group3.pk],
        'username': 'new_clinical_user',
    }
    # assert the user and groups are updated in the database
    clinical_user = ClinicalStaff.objects.get(pk=user.pk)
    assert clinical_user.username == 'new_clinical_user'
    assert clinical_user.groups.count() == 3


def test_api_remove_group_from_user_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of removing a user from a group."""
    api_client.force_login(user=admin_user)
    # add two groups
    group1 = user_factories.GroupFactory(name='group1')
    group2 = user_factories.GroupFactory(name='group2')
    # add one user and add it to one group
    user = user_factories.ClinicalStaff()
    group1.user_set.add(user)
    group2.user_set.add(user)

    # test retrieve
    response = api_client.get(reverse(
        'api:users-detail',
        kwargs={'username': user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data == {'groups': [group1.pk, group2.pk]}
    assert len(response.data['groups']) == 2

    # change the groups of the user by adding one more group
    response.data['groups'].remove(group1.pk)
    data = {
        'groups': response.data['groups'],
        'username': user.username,
    }
    response_put = api_client.put(
        reverse(
            'api:users-detail',
            kwargs={'username': user.username},
        ),
        data=data,
    )
    # test if retrieve gets all user groups and if the user groups are updated
    assert response_put.status_code == HTTPStatus.OK
    assert len(response_put.data['groups']) == 1
    assert response_put.data == {
        'groups': [group2.pk],
        'username': user.username,
    }


def test_userviewset_create_user_password(admin_api_client: APIClient) -> None:
    """The user is created with the correct password hash."""
    password = '123456Opal!!'  # noqa: S105
    data = {
        'username': 'testuser',
        'password': password,
        'password2': password,
    }

    response = admin_api_client.post(reverse('api:users-list'), data=data)

    assert response.status_code == HTTPStatus.CREATED

    user = User.objects.get(username='testuser')
    assert user.check_password(password)
    # ensure the password was not stored raw
    assert user.password != password


def test_userviewset_create_user_no_password(admin_api_client: APIClient) -> None:
    """The user is created with no password."""
    data = {
        'username': 'testuser',
    }

    response = admin_api_client.post(reverse('api:users-list'), data=data)

    assert response.status_code == HTTPStatus.CREATED

    user = User.objects.get(username='testuser')
    assert user.password == ''  # noqa: S105


def test_userviewset_create_user_password_mismatch(admin_api_client: APIClient) -> None:
    """The serializer fails when the passwords don't match."""
    data = {
        'username': 'testuser',
        'password': '123456Opal!!',
        'password2': 'bar',
    }

    response = admin_api_client.post(reverse('api:users-list'), data=data)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "The two password fields don't match" in response.content.decode()


def test_userviewset_create_user_password_invalid(admin_api_client: APIClient) -> None:
    """The serializer fails when the password violates the password requirements."""
    data = {
        'username': 'testuser',
        'password': '12345Opal!!',
        'password2': '12345Opal!!',
    }

    response = admin_api_client.post(reverse('api:users-list'), data=data)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'This password is too short' in response.content.decode()


def test_userviewset_create_user_no_group(admin_api_client: APIClient) -> None:
    """The user is created with no groups."""
    data = {
        'username': 'testuser',
    }

    response = admin_api_client.post(reverse('api:users-list'), data=data)

    assert response.status_code == HTTPStatus.CREATED

    user = User.objects.get(username='testuser')
    assert user.groups.count() == 0


def test_userviewset_create_user_in_group_pass(
    api_client: APIClient,
    user_with_permission: Callable[[str], User],
) -> None:
    """Test the pass of the creation of a new user and adding it to a group."""
    api_client.force_login(user_with_permission('users.add_clinicalstaff'))
    group = user_factories.GroupFactory(name='group1')
    # new user
    data = {
        'username': 'test_user',
        'groups': [group.pk],
    }

    response_post = api_client.post(
        reverse(
            'api:users-list',
        ),
        data=data,
    )

    created_user = User.objects.get(username='test_user')

    # assert that new user is created and assigned to the group as per the post request
    assert response_post.status_code == HTTPStatus.CREATED
    assert created_user.username == 'test_user'
    assert created_user.groups.first() == group


def test_userviewset_create_user_in_multiple_groups_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of the creation of a new user and adding it to multiple groups."""
    api_client.force_login(user=admin_user)
    group1 = user_factories.GroupFactory(name='group1')
    group2 = user_factories.GroupFactory(name='Group2')

    # new user
    data = {
        'username': 'test_user',
        'groups': [group1.pk, group2.pk],
    }

    response_post = api_client.post(
        reverse(
            'api:users-list',
        ),
        data=data,
    )
    created_user = User.objects.get(username='test_user')

    # assert that new user is created and assigned to the group as per the post request
    assert response_post.status_code == HTTPStatus.CREATED
    assert created_user.username == 'test_user'
    assert created_user.groups.count() == 2


def test_userviewset_update_user_password(admin_api_client: APIClient) -> None:
    """The user can be updated with a new password."""
    user: ClinicalStaff = user_factories.ClinicalStaff(username='testuser')
    assert user.check_password('thisisatest')

    token = secrets.token_urlsafe(9)
    data = {
        'username': 'testuser',
        'password': token,
        'password2': token,
        'groups': [],
    }

    response = admin_api_client.put(
        reverse(
            'api:users-detail',
            kwargs={'username': user.username},
        ),
        data=data,
    )

    assert response.status_code == HTTPStatus.OK

    user.refresh_from_db()
    user.check_password(token)
    assert user.password != token, 'password stored raw'


def test_userviewset_update_user_password_unchanged(admin_api_client: APIClient) -> None:
    """The user can be updated without changing the password."""
    user: ClinicalStaff = user_factories.ClinicalStaff(username='testuser')

    data = {
        'username': 'testuser',
        'groups': [],
    }

    response = admin_api_client.put(
        reverse(
            'api:users-detail',
            kwargs={'username': user.username},
        ),
        data=data,
    )

    assert response.status_code == HTTPStatus.OK

    user.refresh_from_db()
    user.check_password('thisisatest')


def test_userviewset_update_user_in_group_with_permission(
    api_client: APIClient,
    user_with_permission: Callable[[str], User],
) -> None:
    """Test the pass of the updating a user group(s) when user has the right permission."""
    api_client.force_login(user_with_permission('users.change_clinicalstaff'))

    # add two groups
    group1 = user_factories.GroupFactory(name='group1')
    group2 = user_factories.GroupFactory(name='group2')

    # add one user
    clinical_user = user_factories.ClinicalStaff()

    # adding clinical user to another group
    data = {
        'groups': [group1.pk, group2.pk],
        'username': clinical_user.username,
    }
    response_put = api_client.put(
        reverse(
            'api:users-detail',
            kwargs={'username': clinical_user.username},
        ),
        data=data,
    )

    # test if retrieve gets all user groups and if the user groups are updated
    assert response_put.status_code == HTTPStatus.OK
    assert len(response_put.data['groups']) == 2
    assert response_put.data == {
        'groups': [group1.pk, group2.pk],
        'username': clinical_user.username,
    }


def test_userviewset_create_user_in_group_existing_user(admin_api_client: APIClient) -> None:
    """Test the fail of the creating when user already exists."""
    # add one user
    clinical_user = user_factories.ClinicalStaff()

    # add one group
    group = user_factories.GroupFactory(name='group1')
    # preparing data for existing user and assign a group to it
    data = {
        'username': clinical_user.username,
        'groups': [group.pk],
    }

    response_post = admin_api_client.post(
        reverse(
            'api:users-list',
        ),
        data=data,
    )
    # assertions
    assert response_post.status_code == HTTPStatus.BAD_REQUEST
    assert response_post.data['username'][0] == 'A user with that username already exists.'


def test_userviewset_set_manager_user_action_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of setting a user group using the action `set_manager_user`."""
    api_client.force_login(user=admin_user)

    user_factories.GroupFactory()
    manager_group = user_factories.GroupFactory(name=USER_MANAGER_GROUP_NAME)

    # add one user
    clinical_user = user_factories.ClinicalStaff()

    # assert user does not have any group yet
    assert not clinical_user.groups.all()

    response = api_client.put(reverse(
        'api:users-set-manager-user',
        kwargs={'username': clinical_user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data['detail'] == 'User was added to the managers group successfully.'
    assert clinical_user.groups.get(pk=manager_group.pk)


def test_userviewset_unset_manager_user_action_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of unsetting a user group using the action `unset_manager_user`."""
    api_client.force_login(user=admin_user)

    user_factories.GroupFactory()
    manager_group = user_factories.GroupFactory(name=USER_MANAGER_GROUP_NAME)

    # add one user
    clinical_user = user_factories.ClinicalStaff()
    clinical_user.groups.add(manager_group)

    response = api_client.put(reverse(
        'api:users-unset-manager-user',
        kwargs={'username': clinical_user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data['detail'] == 'User was removed from the managers group successfully.'
    assert not clinical_user.groups.all()


def test_userviewset_set_manager_wrong_user_action_fail(api_client: APIClient, admin_user: User) -> None:
    """Test the fail of setting manager group of a wrong user using the action `set_manager_user`."""
    api_client.force_login(user=admin_user)

    user_factories.GroupFactory()
    user_factories.GroupFactory(name=USER_MANAGER_GROUP_NAME)

    response = api_client.put(reverse(
        'api:users-set-manager-user',
        kwargs={'username': 'not_exist_user'},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert str(response.data['detail']) == 'No ClinicalStaff matches the given query.'


def test_userviewset_unset_manager_wrong_user_action_fail(api_client: APIClient, admin_user: User) -> None:
    """Test the fail of unsetting manager group of a wrong user using the action `unset_manager_user`."""
    api_client.force_login(user=admin_user)

    user_factories.GroupFactory()
    user_factories.GroupFactory(name=USER_MANAGER_GROUP_NAME)

    response = api_client.put(reverse(
        'api:users-unset-manager-user',
        kwargs={'username': 'not_exist_user'},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert str(response.data['detail']) == 'No ClinicalStaff matches the given query.'


def test_userviewset_set_manager_no_group_action_fail(api_client: APIClient, admin_user: User) -> None:
    """Test the fail of setting a user group when manager group does not exist using the action `set_manager_user`."""
    api_client.force_login(user=admin_user)

    user_factories.GroupFactory()
    clinical_user = user_factories.ClinicalStaff()

    response = api_client.put(reverse(
        'api:users-set-manager-user',
        kwargs={'username': clinical_user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert str(response.data['detail']) == 'Manager group not found.'


def test_userviewset_unset_manager_no_group_action_fail(api_client: APIClient, admin_user: User) -> None:
    """Test the fail of unsetting a user group when manager group does not exist using the action `set_manager_user`."""
    api_client.force_login(user=admin_user)

    user_factories.GroupFactory()
    clinical_user = user_factories.ClinicalStaff()

    response = api_client.put(reverse(
        'api:users-unset-manager-user',
        kwargs={'username': clinical_user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert str(response.data['detail']) == 'Manager group not found.'


def test_api_deactivate_user_action_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of deactivating a user the action `deactivate-user`."""
    api_client.force_login(user=admin_user)

    # add one user
    clinical_user = user_factories.ClinicalStaff()

    response = api_client.put(reverse(
        'api:users-deactivate-user',
        kwargs={'username': clinical_user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data['detail'] == 'User was deactivated successfully.'
    assert not User.objects.get(username=clinical_user.username).is_active


def test_api_deactivate_user_action_fail(api_client: APIClient, admin_user: User) -> None:
    """Test the fail case of deactivating a non-exist user using the action `deactivate-user`."""
    api_client.force_login(user=admin_user)

    response = api_client.put(reverse(
        'api:users-deactivate-user',
        kwargs={'username': 'not_exist_user'},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.data['detail'] == 'No ClinicalStaff matches the given query.'


def test_api_reactivate_user_action_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of reactivating a user the action `reactivate-user`."""
    api_client.force_login(user=admin_user)

    # add one user
    clinical_user = user_factories.ClinicalStaff(is_active=False)

    response = api_client.put(reverse(
        'api:users-reactivate-user',
        kwargs={'username': clinical_user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data['detail'] == 'User was reactivated successfully.'
    assert User.objects.get(username=clinical_user.username).is_active


def test_api_reactivate_user_action_fail(api_client: APIClient, admin_user: User) -> None:
    """Test the fail case of reactivating a non-exist user using the action `reactivate-user`."""
    api_client.force_login(user=admin_user)

    response = api_client.put(reverse(
        'api:users-reactivate-user',
        kwargs={'username': 'not_exist_user'},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.data['detail'] == 'No ClinicalStaff matches the given query.'
