from django_test_migrations.migrator import Migrator

from .. import models


def test_migration_relationshiptype_prepopulate_no_existing_types(migrator: Migrator) -> None:
    """Ensure the migration correctly prepopulates the relationshiptypes."""
    old_state = migrator.apply_initial_migration(('patients', '0010_relationshiptype_role'))
    RelationshipType = old_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 0

    RelationshipType.objects.create(
        name='self',
        name_en='Self',
        name_fr='Soi',
        description='The patient is the requestor',
        description_en='The patient is the requestor',
        description_fr='Le patient est le demandeur',
        start_age=10,
    )

    new_state = migrator.apply_tested_migration(('patients', '0011_prepopulate_relationshiptype'))

    RelationshipType = new_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 2
    assert RelationshipType.objects.filter(role_type=models.RoleType.SELF).count() == 1
    assert RelationshipType.objects.filter(role_type=models.RoleType.PARENTGUARDIAN).count() == 1

    # ensure that the migration can be reversed without any error
    migrator.apply_tested_migration(('patients', '0010_relationshiptype_role'))

    assert RelationshipType.objects.count() == 2


# def test_migration_relationshiptype_prepopulate_existing_role_types(migrator: Migrator) -> None:
#     """Ensure the migration correctly prepopulates the relationshiptypes."""
#     old_state = migrator.apply_initial_migration(('patients', '0010_relationshiptype_role'))
#     RelationshipType = old_state.apps.get_model('patients', 'RelationshipType')

#     RelationshipType.objects.create(
#         name='self',
#         name_en='Self',
#         name_fr='Soi',
#         description='The patient is the requestor',
#         description_en='The patient is the requestor',
#         description_fr='Le patient est le demandeur',
#         start_age=10,
#         role_type=models.RoleType.SELF,
#     )

#     RelationshipType.objects.create(
#         name='Guardian',
#         name_en='Guardian',
#         name_fr='Gardien',
#         description='A parent or guardian of the patient',
#         description_en='A parent or guardian of the patient',
#         description_fr='Un parent ou un tuteur du patient',
#         start_age=0,
#         role_type=models.RoleType.PARENTGUARDIAN,
#     )

#     new_state = migrator.apply_tested_migration(('patients', '0011_prepopulate_relationshiptype'))

#     RelationshipType = new_state.apps.get_model('patients', 'RelationshipType')

#     assert RelationshipType.objects.count() == 2
#     assert RelationshipType.objects.filter(role_type=models.RoleType.CAREGIVER).count() == 0

#     # ensure that the migration can be reversed without any error
#     migrator.apply_tested_migration(('patients', '0010_relationshiptype_role'))

#     assert RelationshipType.objects.count() == 2


# def test_migration_relationshiptype_reverse(migrator: Migrator) -> None:
#     """Ensure the migration correctly prepopulates the relationshiptypes."""
#     db_state = migrator.apply_initial_migration(('patients', '0011_prepopulate_relationshiptype'))
#     db_state = migrator.apply_initial_migration(('patients', '0010_relationshiptype_role'))

#     RelationshipType = db_state.apps.get_model('patients', 'RelationshipType')

#     prepopulated_type_self = RelationshipType.objects.filter(role_type=models.RoleType.SELF)
#     prepopulated_type_parent = RelationshipType.objects.filter(role_type=models.RoleType.PARENTGUARDIAN)

#     assert not prepopulated_type_self
#     assert not prepopulated_type_parent

#     migrator.reset()
