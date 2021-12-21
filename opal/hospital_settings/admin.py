from django.contrib import admin

from .models import Institution, Site

admin.site.register(Institution, admin.ModelAdmin)
admin.site.register(Site, admin.ModelAdmin)
