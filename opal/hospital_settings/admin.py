from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from .models import Institution, Site


# need to use modeltranslation's admin
# see: https://django-modeltranslation.readthedocs.io/en/latest/admin.html
class InstitutionAdmin(TranslationAdmin):
    pass


class SiteAdmin(TranslationAdmin):
    pass


admin.site.register(Institution, InstitutionAdmin)
admin.site.register(Site, SiteAdmin)
