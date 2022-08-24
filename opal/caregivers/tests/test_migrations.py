from django_test_migrations.migrator import Migrator


def test_migration_caregiverprofile_uuid(migrator: Migrator) -> None:
    """Ensure the uuid field can be added for multiple model instances."""
    old_state = migrator.apply_initial_migration(('caregivers', '0003_securityquestion'))
    CaregiverProfile = old_state.apps.get_model('caregivers', 'CaregiverProfile')
    User = old_state.apps.get_model('users', 'User')

    user1 = User.objects.create(username='test')
    CaregiverProfile.objects.create(user=user1)
    user2 = User.objects.create(username='test2')
    CaregiverProfile.objects.create(user=user2)

    # ensure that the migration can be applied without problems
    new_state = migrator.apply_tested_migration(('caregivers', '0004_caregiverprofile_uuid'))

    CaregiverProfile = new_state.apps.get_model('caregivers', 'CaregiverProfile')

    caregiver1 = CaregiverProfile.objects.all()[0]
    caregiver2 = CaregiverProfile.objects.all()[1]

    assert caregiver1.uuid != caregiver2.uuid


def test_migration_caregiverprofile_uuid_reverse(migrator: Migrator) -> None:
    """Ensure the uuid migration can be reversed."""
    old_state = migrator.apply_initial_migration(('caregivers', '0004_caregiverprofile_uuid'))
    CaregiverProfile = old_state.apps.get_model('caregivers', 'CaregiverProfile')
    User = old_state.apps.get_model('users', 'User')

    user1 = User.objects.create(username='test')
    CaregiverProfile.objects.create(user=user1)
    user2 = User.objects.create(username='test2')
    CaregiverProfile.objects.create(user=user2)

    # ensure that the migration can be reversed without problems
    migrator.apply_tested_migration(('caregivers', '0003_securityquestion'))
