from django_test_migrations.migrator import Migrator

from .. import models


def test_migration_relationshiptype_prepopulate(migrator: Migrator) -> None:
    """Ensure the migration correctly prepopulates the relationshiptypes."""
    db_state = migrator.apply_initial_migration(('patients', '0011_prepopulate_relationshiptype'))
    RelationshipType = db_state.apps.get_model('patients', 'RelationshipType')

    prepopulated_types = RelationshipType.objects.all()
    prepopulated_type_self = RelationshipType.objects.filter(role_type=models.RoleType.SELF)
    prepopulated_type_parent = RelationshipType.objects.filter(role_type=models.RoleType.PARENTGUARDIAN)

    assert len(prepopulated_types) == 2
    assert prepopulated_type_self is not None
    assert prepopulated_type_parent is not None
    assert prepopulated_type_self.count() == 1
    assert prepopulated_type_parent.count() == 1

    migrator.reset()


def test_migration_relationshiptype_reverse(migrator: Migrator) -> None:
    """Ensure the migration correctly prepopulates the relationshiptypes."""
    db_state = migrator.apply_initial_migration(('patients', '0011_prepopulate_relationshiptype'))
    db_state = migrator.apply_initial_migration(('patients', '0010_relationshiptype_role'))

    RelationshipType = db_state.apps.get_model('patients', 'RelationshipType')

    prepopulated_type_self = RelationshipType.objects.filter(role_type=models.RoleType.SELF)
    prepopulated_type_parent = RelationshipType.objects.filter(role_type=models.RoleType.PARENTGUARDIAN)

    assert not prepopulated_type_self
    assert not prepopulated_type_parent

    migrator.reset()
