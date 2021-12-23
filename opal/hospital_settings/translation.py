from modeltranslation.translator import TranslationOptions, register

from .models import Institution, Site


@register([Institution, Site])
class LocationTranslationOptions(TranslationOptions):
    fields = ('name', 'parking_url')
