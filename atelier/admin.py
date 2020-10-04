from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.http import urlencode

from .models import User
from .models import Atelier
from django.contrib import admin

admin.site.register(User, UserAdmin)
UserAdmin.list_display += ('occupation', 'atelier',)
UserAdmin.list_filter += ('atelier',)
UserAdmin.fieldsets[1][1]['fields'] += ('is_administrator', 'phone_number', 'atelier', 'occupation')


# admin.site.register(Atelier)

# @admin.register(User)
# class UsersAdmin(admin.ModelAdmin):
#     pass

def custom_titled_filter(title):
    """
    provide the filter title
    """

    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance

    return Wrapper


@admin.register(Atelier)
class AtelierAdmin(admin.ModelAdmin):
    list_filter = (
        ('place', custom_titled_filter('Place')),
        ('user__email', custom_titled_filter('User email')),
    )
    list_display = ['id', 'name', 'place', 'show_user_quantity', 'created_datetime']

    def show_user_quantity(self, obj):
        from django.utils.html import format_html
        user_quantity = Atelier.objects.filter(user__atelier=obj).count()
        url = (
                reverse("admin:atelier_user_changelist")
                + "?"
                + urlencode({"atelier__id": f'{obj.id}'})
        )
        return format_html('<a href="{}">{} Users</a>', url, user_quantity)

    show_user_quantity.short_description = 'Users quantity'
