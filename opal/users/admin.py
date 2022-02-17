"""Module providing admin functionality for the users app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

# use Django's default UserAdmin for now (until the User is actually customized)
admin.site.register(User, UserAdmin)
