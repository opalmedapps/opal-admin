from modeltranslation.translator import TranslationOptions, register

from .models import Institution, Site


@register(Institution)
class InstitutionTranslationOptions(TranslationOptions):
    fields = ('name', )


@register(Site)
class SiteTranslationOptions(TranslationOptions):
    fields = ('name', 'parking_url', )
