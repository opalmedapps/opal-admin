from django.db import models

from ..dbrouters import LegacyDbRouter


# Create fake model classes to simulate managed and unmanaged models
# At runtime Django's model._meta.app_label
# does not return the fully qualified name, e.g., core instead of opal.core
class ManagedModel(models.Model):  # noqa: D101,DJ08,DJ10,DJ11
    class Meta:
        app_label = 'core'


class LegacyModel(models.Model):  # noqa: D101,DJ08,DJ10,DJ11
    class Meta:
        app_label = 'legacy'
        managed = False


class LegacyQuestionnaireModel(models.Model):  # noqa: D101,DJ08,DJ10,DJ11
    class Meta:
        app_label = 'legacy_questionnaires'
        managed = False


def test_legacydbrouter_managed_read() -> None:
    """Ensure that regular (managed) models use the default DB connection."""
    router = LegacyDbRouter()

    assert router.db_for_read(ManagedModel) is None


def test_legacydbrouter_unmanaged_read() -> None:
    """Ensure that legacy (unmanaged) models use the legacy DB connection."""
    router = LegacyDbRouter()

    assert router.db_for_read(LegacyModel) == 'legacy'


def test_legacyquestionnaire_dbrouter_unmanaged_read() -> None:
    """Ensure that legacy questionnaire (unmanaged) models use the legacy QuestionnaireDB connection."""
    router = LegacyDbRouter()

    assert router.db_for_read(LegacyQuestionnaireModel) == 'questionnaire'


def test_legacydbrouter_managed_write() -> None:
    """Ensure that regular (managed) models use the default DB connection."""
    router = LegacyDbRouter()

    assert router.db_for_write(ManagedModel) is None


def test_legacydbrouter_unmanaged_write() -> None:
    """Ensure that legacy (unmanaged) models use the legacy DB connection."""
    router = LegacyDbRouter()

    assert router.db_for_write(LegacyModel) == 'legacy'


def test_legacyquestionnaire_dbrouter_unmanaged_write() -> None:
    """Ensure that legacy questionnaire (unmanaged) models use the legacy QuestionnaireDB connection."""
    router = LegacyDbRouter()

    assert router.db_for_write(LegacyQuestionnaireModel) == 'questionnaire'
