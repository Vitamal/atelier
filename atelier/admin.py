from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Atelier
from django.utils.translation import gettext, gettext_lazy as _

admin.site.register(User, UserAdmin)
UserAdmin.list_display += ('occupation', 'atelier',)
UserAdmin.list_filter += ('atelier',)
UserAdmin.fieldsets += ((_('Additional info'), {'fields': ('is_administrator', 'phone_number', 'atelier', 'occupation')}),)

admin.site.register(Atelier)


# @admin.register(User)
# class UsersAdmin(admin.ModelAdmin):
#     pass

# @admin.register(Atelier)
# class AtelierAdmin(admin.ModelAdmin):
#     pass
