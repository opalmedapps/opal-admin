from typing import Type

from django.db.models import Model

from django_test_migrations.migrator import Migrator

from .. import models


def test_migration_relationshiptype_prepopulate_no_existing_types(migrator: Migrator) -> None:
    """Ensure the migration correctly prepopulates the relationshiptypes."""
    old_state = migrator.apply_initial_migration(('patients', '0013_relationshiptype_role'))  # noqa: WPS204
    RelationshipType = old_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 0

    new_state = migrator.apply_tested_migration(('patients', '0014_prepopulate_relationshiptype'))

    RelationshipType = new_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 2
    assert RelationshipType.objects.filter(role_type=models.RoleType.SELF).count() == 1
    assert RelationshipType.objects.filter(role_type=models.RoleType.PARENT_GUARDIAN).count() == 1

    # ensure that the migration can be reversed without any error
    migrator.apply_tested_migration(('patients', '0013_relationshiptype_role'))

    assert RelationshipType.objects.count() == 2


def test_migration_relationshiptype_prepopulate_existing_types(migrator: Migrator) -> None:
    """Ensure the migration correctly prepopulates the relationshiptypes."""
    old_state = migrator.apply_initial_migration(('patients', '0013_relationshiptype_role'))
    RelationshipType = old_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 0

    # add pre-existing types
    RelationshipType.objects.create(
        name='Self',
        name_en='Self',
        name_fr='Soi',
        description='The patient is the requestor',
        description_en='The patient is the requestor',
        description_fr='Le patient est le demandeur',
        start_age=14,
    )
    RelationshipType.objects.create(
        name='Guardian',
        name_en='Guardian',
        name_fr='Gardien',
        description='A parent or guardian of the patient',
        description_en='A parent or guardian of the patient',
        description_fr='Un parent ou un tuteur du patient',
        start_age=0,
        end_age=14,
    )

    new_state = migrator.apply_tested_migration(('patients', '0014_prepopulate_relationshiptype'))

    RelationshipType = new_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 2
    assert RelationshipType.objects.filter(role_type=models.RoleType.SELF).count() == 1
    assert RelationshipType.objects.filter(role_type=models.RoleType.PARENT_GUARDIAN).count() == 1

    # ensure that the migration can be reversed without any error
    migrator.apply_tested_migration(('patients', '0013_relationshiptype_role'))

    assert RelationshipType.objects.count() == 2


def test_migration_relationshiptype_prepopulate_existing_role_types(migrator: Migrator) -> None:
    """Ensure the migration correctly prepopulates the relationshiptypes."""
    old_state = migrator.apply_initial_migration(('patients', '0013_relationshiptype_role'))
    RelationshipType = old_state.apps.get_model('patients', 'RelationshipType')

    RelationshipType.objects.create(
        name='Self',
        name_en='Self',
        name_fr='Soi',
        description='The patient is the requestor',
        description_en='The patient is the requestor',
        description_fr='Le patient est le demandeur',
        start_age=14,
        role_type=models.RoleType.SELF,
    )

    RelationshipType.objects.create(
        name='Guardian',
        name_en='Guardian',
        name_fr='Gardien',
        description='A parent or guardian of the patient',
        description_en='A parent or guardian of the patient',
        description_fr='Un parent ou un tuteur du patient',
        start_age=0,
        end_age=14,
        role_type=models.RoleType.PARENT_GUARDIAN,
    )

    new_state = migrator.apply_tested_migration(('patients', '0014_prepopulate_relationshiptype'))

    RelationshipType = new_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 2
    assert RelationshipType.objects.filter(role_type=models.RoleType.CAREGIVER).count() == 0

    # ensure that the migration can be reversed without any error
    migrator.apply_tested_migration(('patients', '0013_relationshiptype_role'))

    assert RelationshipType.objects.count() == 2


def test_migration_relationshiptype_prepopulate_existing_caregiver(migrator: Migrator) -> None:
    """Ensure the migration correctly prepopulates the relationshiptypes."""
    old_state = migrator.apply_initial_migration(('patients', '0013_relationshiptype_role'))
    RelationshipType = old_state.apps.get_model('patients', 'RelationshipType')

    RelationshipType.objects.create(
        name='Caregiver',
        name_en='Caregiver',
        name_fr='Aidant',
        description='A caregiver',
        description_en='A caregiver',
        description_fr='Un proche aidant',
        start_age=16,
        role_type=models.RoleType.CAREGIVER,
    )

    RelationshipType.objects.create(
        name='Guardian',
        name_en='Guardian',
        name_fr='Gardien',
        description='A parent or guardian of the patient',
        description_en='A parent or guardian of the patient',
        description_fr='Un parent ou un tuteur du patient',
        start_age=0,
        end_age=14,
        role_type=models.RoleType.PARENT_GUARDIAN,
    )

    new_state = migrator.apply_tested_migration(('patients', '0014_prepopulate_relationshiptype'))

    RelationshipType = new_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 3
    assert RelationshipType.objects.filter(role_type=models.RoleType.CAREGIVER).count() == 1

    # ensure that the migration can be reversed without any error
    migrator.apply_tested_migration(('patients', '0013_relationshiptype_role'))

    assert RelationshipType.objects.count() == 3


def _create_patient(model: Type[Model], ramq: str = '') -> Model:
    return model.objects.create(
        first_name='Marge',
        last_name='Simpson',
        date_of_birth='1987-03-19',
        sex=models.Patient.SexType.FEMALE,
    )


def test_migration_patient_uuid(migrator: Migrator) -> None:
    """Ensure the uuid field can be added for multiple model instances."""
    old_state = migrator.apply_initial_migration(('patients', '0016_add_manage_relationshiptype_permission'))
    Patient = old_state.apps.get_model('patients', 'Patient')

    _create_patient(Patient)
    _create_patient(Patient, ramq='SIMM87531908')

    # ensure that the migration can be applied without problems
    new_state = migrator.apply_tested_migration(('patients', '0017_add_patient_uuid'))

    Patient = new_state.apps.get_model('patients', 'Patient')

    patient1 = Patient.objects.all()[0]
    patient2 = Patient.objects.all()[1]

    assert patient1.uuid != patient2.uuid


def test_migration_patient_uuid_reverse(migrator: Migrator) -> None:
    """Ensure the uuid migration can be reversed."""
    old_state = migrator.apply_initial_migration(('patients', '0017_add_patient_uuid'))
    Patient = old_state.apps.get_model('patients', 'Patient')

    _create_patient(Patient)
    _create_patient(Patient, ramq='SIMM87531908')

    # ensure that the migration can be reversed without problems
    migrator.apply_tested_migration(('patients', '0016_add_manage_relationshiptype_permission'))


def test_migration_relationshiptype_existing_role_types_updated(migrator: Migrator) -> None:  # noqa: WPS218
    """Ensure the migration correctly updates the existing relationshiptypes."""
    old_state = migrator.apply_initial_migration(('patients', '0017_add_patient_uuid'))
    RelationshipType = old_state.apps.get_model('patients', 'RelationshipType')

    self_type = RelationshipType.objects.get(role_type=models.RoleType.SELF)
    parent_type = RelationshipType.objects.get(role_type=models.RoleType.PARENT_GUARDIAN)

    assert self_type.form_required is True
    assert self_type.can_answer_questionnaire is False
    assert parent_type.can_answer_questionnaire is False

    migrator.apply_tested_migration(('patients', '0018_update_existing_relationshiptypes'))

    self_type.refresh_from_db()
    parent_type.refresh_from_db()

    assert self_type.form_required is False
    assert self_type.can_answer_questionnaire is True
    assert parent_type.can_answer_questionnaire is True


def test_migration_relationshiptype_add_remaining_types(migrator: Migrator) -> None:
    """Ensure the migration correctly prepopulates the relationshiptypes."""
    old_state = migrator.apply_initial_migration(('patients', '0018_update_existing_relationshiptypes'))  # noqa: WPS204
    RelationshipType = old_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 2

    new_state = migrator.apply_tested_migration(('patients', '0019_add_remaining_default_relationshiptypes'))

    RelationshipType = new_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 4
    assert RelationshipType.objects.filter(role_type=models.RoleType.GUARDIAN_CAREGIVER).count() == 1
    assert RelationshipType.objects.filter(role_type=models.RoleType.MANDATARY).count() == 1

    # ensure that the migration can be reversed without any error
    migrator.apply_tested_migration(('patients', '0018_update_existing_relationshiptypes'))

    assert RelationshipType.objects.count() == 4


def test_migration_relationshiptype_update_existing_types(migrator: Migrator) -> None:  # noqa: WPS218
    """Ensure the migration correctly prepopulates the relationshiptypes for Guardian-Caregiver and Mandatary."""
    old_state = migrator.apply_initial_migration(('patients', '0018_update_existing_relationshiptypes'))
    RelationshipType = old_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 2

    # add pre-existing types
    guardian_caregiver = RelationshipType.objects.create(
        name='Guardian-Caregiver',
        name_en='Guardian-Caregiver',
        name_fr='Gardien-Proche aidant',
        description='Guardian-Caregiver Description EN',
        description_en='Guardian-Caregiver Description EN',
        description_fr='Guardian-Caregiver Description FR',
        start_age=14,
    )
    mandatary = RelationshipType.objects.create(
        name='Mandatary',
        name_en='Mandatary',
        name_fr='Mandataire',
        description='Mandatary Description EN',
        description_en='Mandatary Description EN',
        description_fr='Mandatary Description FR',
        start_age=0,
    )

    new_state = migrator.apply_tested_migration(('patients', '0019_add_remaining_default_relationshiptypes'))

    RelationshipType = new_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 4
    assert RelationshipType.objects.filter(role_type=models.RoleType.GUARDIAN_CAREGIVER).count() == 1
    assert RelationshipType.objects.filter(role_type=models.RoleType.MANDATARY).count() == 1

    guardian_caregiver.refresh_from_db()
    mandatary.refresh_from_db()

    assert guardian_caregiver.role_type == models.RoleType.GUARDIAN_CAREGIVER
    assert mandatary.role_type == models.RoleType.MANDATARY

    # ensure that the migration can be reversed without any error
    migrator.apply_tested_migration(('patients', '0018_update_existing_relationshiptypes'))

    assert RelationshipType.objects.count() == 4


def test_migration_relationshiptype_existing_role_types_untouched(migrator: Migrator) -> None:
    """Ensure the migration correctly prepopulates the relationshiptypes."""
    old_state = migrator.apply_initial_migration(('patients', '0018_update_existing_relationshiptypes'))
    RelationshipType = old_state.apps.get_model('patients', 'RelationshipType')

    RelationshipType.objects.create(
        name='Guardian-Caregiver',
        name_en='Guardian-Caregiver',
        name_fr='Gardien-Proche aidant',
        description='Guardian-Caregiver Description EN',
        description_en='Guardian-Caregiver Description EN',
        description_fr='Guardian-Caregiver Description FR',
        start_age=14,
        role_type=models.RoleType.GUARDIAN_CAREGIVER,
    )
    RelationshipType.objects.create(
        name='Mandatary',
        name_en='Mandatary',
        name_fr='Mandataire',
        description='Mandatary Description EN',
        description_en='Mandatary Description EN',
        description_fr='Mandatary Description FR',
        start_age=0,
        role_type=models.RoleType.MANDATARY,
    )

    new_state = migrator.apply_tested_migration(('patients', '0019_add_remaining_default_relationshiptypes'))

    RelationshipType = new_state.apps.get_model('patients', 'RelationshipType')

    assert RelationshipType.objects.count() == 4
    assert RelationshipType.objects.filter(role_type=models.RoleType.CAREGIVER).count() == 0

    # ensure that the migration can be reversed without any error
    migrator.apply_tested_migration(('patients', '0018_update_existing_relationshiptypes'))

    assert RelationshipType.objects.count() == 4
