"""Test module for the `users` app REST API viewsets endpoints."""
from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.users import factories as user_factories
from opal.users.models import ClinicalStaff, User

pytestmark = pytest.mark.django_db


def test_api_retrieve_user_in_group_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of the retrieving user and their group(s)."""
    api_client.force_login(user=admin_user)
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

    # assertions
    assert response.status_code == HTTPStatus.OK
    assert response.data == {'groups': [group.pk]}
    assert len(response.data['groups']) == 1


def test_api_add_group_update_user_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of the updating a user and add to a group."""
    api_client.force_login(user=admin_user)
    # add two groups
    group_1 = user_factories.GroupFactory(name='group1')
    group_2 = user_factories.GroupFactory(name='group2')
    # add one user and add it to one group
    user = user_factories.ClinicalStaff(username='test_clinical_user')
    group_2.user_set.add(user)

    # test retrieve
    response = api_client.get(reverse(
        'api:users-detail',
        kwargs={'username': user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data == {'groups': [group_2.pk]}
    assert len(response.data['groups']) == 1

    # change the groups and the name of the user
    response.data['groups'].append(group_1.pk)
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
        format='json',
    )
    # test if retrieve gets all user groups and if the user groups are updated
    assert response_put.status_code == HTTPStatus.OK
    assert len(response_put.data['groups']) == 2
    assert response_put.data == {
        'groups': [group_1.pk, group_2.pk],
        'username': 'new_clinical_user',
    }
    # assert the user and groups are updated in the database
    clinical_user = ClinicalStaff.objects.get(pk=user.pk)
    assert clinical_user.username == 'new_clinical_user'
    assert clinical_user.groups.count() == 2


def test_api_add_multiple_groups_to_user_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of editing a user and add to multiple groups."""
    api_client.force_login(user=admin_user)
    # add two groups
    group_1 = user_factories.GroupFactory(name='group1')
    group_2 = user_factories.GroupFactory(name='group2')
    group_3 = user_factories.GroupFactory(name='group3')

    # add one user and add it to one group
    user = user_factories.ClinicalStaff()
    group_2.user_set.add(user)

    # test retrieve
    response = api_client.get(reverse(
        'api:users-detail',
        kwargs={'username': user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data == {'groups': [group_2.pk]}
    assert len(response.data['groups']) == 1

    # change the groups of the user by adding one more group
    response.data['groups'].append(group_1.pk)
    response.data['groups'].append(group_3.pk)

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
        format='json',
    )
    # test if retrieve gets all user groups and if the user groups are updated
    assert response_put.status_code == HTTPStatus.OK
    assert len(response_put.data['groups']) == 3
    assert response_put.data == {
        'groups': [group_1.pk, group_2.pk, group_3.pk],
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
    group_1 = user_factories.GroupFactory(name='group1')
    group_2 = user_factories.GroupFactory(name='group2')
    # add one user and add it to one group
    user = user_factories.ClinicalStaff()
    group_1.user_set.add(user)
    group_2.user_set.add(user)

    # test retrieve
    response = api_client.get(reverse(
        'api:users-detail',
        kwargs={'username': user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data == {'groups': [group_1.pk, group_2.pk]}
    assert len(response.data['groups']) == 2

    # change the groups of the user by adding one more group
    response.data['groups'].remove(group_1.pk)
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
        format='json',
    )
    # test if retrieve gets all user groups and if the user groups are updated
    assert response_put.status_code == HTTPStatus.OK
    assert len(response_put.data['groups']) == 1
    assert response_put.data == {
        'groups': [group_2.pk],
        'username': user.username,
    }


def test_api_create_user_in_group_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of the creation of a new user and adding it to a group."""
    api_client.force_login(user=admin_user)
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
        format='json',
    )
    created_user = User.objects.get(username='test_user')

    # assert that new user is created and assigned to the group as per the post request
    assert response_post.status_code == HTTPStatus.CREATED
    assert created_user.username == 'test_user'
    assert created_user.groups.first() == group


def test_api_create_user_in_multiple_groups_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of the creation of a new user and adding it to multiple groups."""
    api_client.force_login(user=admin_user)
    group_1 = user_factories.GroupFactory(name='group1')
    group_2 = user_factories.GroupFactory(name='Group2')

    # new user
    data = {
        'username': 'test_user',
        'groups': [group_1.pk, group_2.pk],
    }

    response_post = api_client.post(
        reverse(
            'api:users-list',
        ),
        data=data,
        format='json',
    )
    created_user = User.objects.get(username='test_user')

    # assert that new user is created and assigned to the group as per the post request
    assert response_post.status_code == HTTPStatus.CREATED
    assert created_user.username == 'test_user'
    assert created_user.groups.count() == 2


def test_api_retrieve_user_in_group_no_permission(api_client: APIClient, django_user_model: User) -> None:
    """Test the fail of the retrieving user and their group(s) when user does not have permission."""
    user = django_user_model.objects.create(username='test_user')
    api_client.force_login(user=user)

    user_factories.GroupFactory()
    group = user_factories.GroupFactory(name='group')
    # add clinical staff user
    clinical_user = user_factories.ClinicalStaff()
    group.user_set.add(clinical_user)

    response = api_client.get(reverse(
        'api:users-detail',
        kwargs={'username': user.username},
    ))

    # assertions
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.data['detail'] == 'You do not have permission to perform this action.'

    # when given the right permission it passes
    view_permission = Permission.objects.get(codename='view_clinicalstaff')
    user.user_permissions.add(view_permission)

    response = api_client.get(reverse(
        'api:users-detail',
        kwargs={'username': clinical_user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data == {'groups': [group.pk]}
    assert len(response.data['groups']) == 1


def test_api_create_user_in_group_no_permission(api_client: APIClient, django_user_model: User) -> None:
    """Test the fail of the creating a new user in a group(s) when user does not have permission."""
    user = django_user_model.objects.create(username='test_user')
    api_client.force_login(user=user)

    group = user_factories.GroupFactory(name='group1')
    # new user
    data = {
        'username': 'api_test_user',
        'groups': [group.pk],
    }

    response_post = api_client.post(
        reverse(
            'api:users-list',
        ),
        data=data,
        format='json',
    )

    # assertions
    assert response_post.status_code == HTTPStatus.FORBIDDEN
    assert response_post.data['detail'] == 'You do not have permission to perform this action.'

    # when given the right permission it passes
    add_permission = Permission.objects.get(codename='add_clinicalstaff')
    user.user_permissions.add(add_permission)

    response_post = api_client.post(
        reverse(
            'api:users-list',
        ),
        data=data,
        format='json',
    )
    created_user = User.objects.get(username='api_test_user')
    # assert that new user is created and assigned to the group as per the post request
    assert response_post.status_code == HTTPStatus.CREATED
    assert created_user.username == 'api_test_user'
    assert created_user.groups.first() == group


def test_api_update_user_in_group_no_permission(api_client: APIClient, django_user_model: User) -> None:
    """Test the fail of the updating a user group(s) when user does not have permission."""
    user = django_user_model.objects.create(username='test_user')
    api_client.force_login(user=user)

    # add group
    group = user_factories.GroupFactory(name='group')

    # add one user and add it to one group
    user = user_factories.ClinicalStaff()
    group.user_set.add(user)

    groups = {'groups': [group.pk]}
    response_put = api_client.put(
        reverse(
            'api:users-detail',
            kwargs={'username': user.username},
        ),
        data=groups,
        format='json',
    )
    # assertions
    assert response_put.status_code == HTTPStatus.FORBIDDEN
    assert response_put.data['detail'] == 'You do not have permission to perform this action.'


def test_api_get_user_group_with_permission(api_client: APIClient, django_user_model: User) -> None:
    """Test the pass of the retrieving user and their group(s) when user has the right permission."""
    user = django_user_model.objects.create(username='test_user')
    api_client.force_login(user=user)

    user_factories.GroupFactory()
    group = user_factories.GroupFactory(name='group')
    # add clinical staff user
    clinical_user = user_factories.ClinicalStaff()
    group.user_set.add(clinical_user)

    # when given the right permission it passes
    view_permission = Permission.objects.get(codename='view_clinicalstaff')
    user.user_permissions.add(view_permission)

    response = api_client.get(reverse(
        'api:users-detail',
        kwargs={'username': clinical_user.username},
    ))

    # assert retrieved info
    assert response.status_code == HTTPStatus.OK
    assert response.data == {'groups': [group.pk]}
    assert len(response.data['groups']) == 1


def test_api_create_user_in_group_with_permission(api_client: APIClient, django_user_model: User) -> None:
    """Test the pass of the creating a new user in a group(s) when user has the right permission."""
    user = django_user_model.objects.create(username='test_user')
    # granting the right permission
    add_permission = Permission.objects.get(codename='add_clinicalstaff')
    user.user_permissions.add(add_permission)
    api_client.force_login(user=user)

    group = user_factories.GroupFactory(name='group1')
    # preparing data for new user and assign a group to it
    data = {
        'username': 'api_test_user',
        'groups': [group.pk],
    }

    response_post = api_client.post(
        reverse(
            'api:users-list',
        ),
        data=data,
        format='json',
    )
    created_user = User.objects.get(username='api_test_user')
    # assert that new user is created and assigned to the group as per the post request
    assert response_post.status_code == HTTPStatus.CREATED
    assert created_user.username == 'api_test_user'
    assert created_user.groups.first() == group


def test_api_update_user_in_group_with_permission(api_client: APIClient, django_user_model: User) -> None:
    """Test the pass of the updating a user group(s) when user has the right permission."""
    user = django_user_model.objects.create(username='test_user')
    # giving the right permission
    change_permission = Permission.objects.get(codename='change_clinicalstaff')
    user.user_permissions.add(change_permission)

    api_client.force_login(user=user)

    # add two groups
    group_1 = user_factories.GroupFactory(name='group1')
    group_2 = user_factories.GroupFactory(name='group2')

    # add one user
    clinical_user = user_factories.ClinicalStaff()

    # adding clinical user to another group
    data = {
        'groups': [group_1.pk, group_2.pk],
        'username': clinical_user.username,
    }
    response_put = api_client.put(
        reverse(
            'api:users-detail',
            kwargs={'username': clinical_user.username},
        ),
        data=data,
        format='json',
    )

    # test if retrieve gets all user groups and if the user groups are updated
    assert response_put.status_code == HTTPStatus.OK
    assert len(response_put.data['groups']) == 2
    assert response_put.data == {
        'groups': [group_1.pk, group_2.pk],
        'username': clinical_user.username,
    }


def test_api_create_user_in_group_existing_user(api_client: APIClient, django_user_model: User) -> None:
    """Test the fail of the creating when user already exists."""
    user = django_user_model.objects.create(username='test_user')
    # granting the right permission
    add_permission = Permission.objects.get(codename='add_clinicalstaff')
    user.user_permissions.add(add_permission)
    api_client.force_login(user=user)

    # add one user
    clinical_user = user_factories.ClinicalStaff()

    # add one group
    group = user_factories.GroupFactory(name='group1')
    # preparing data for existing user and assign a group to it
    data = {
        'username': clinical_user.username,
        'groups': [group.pk],
    }

    response_post = api_client.post(
        reverse(
            'api:users-list',
        ),
        data=data,
        format='json',
    )
    # assertions
    assert response_post.status_code == HTTPStatus.BAD_REQUEST
    assert response_post.data['username'][0] == 'A user with that username already exists.'
