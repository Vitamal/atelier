from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.http import urlencode

from .models import User
from .models import Atelier
from django.contrib import admin

@admin.register(User)
class UsersAdmin(UserAdmin):
    list_display = ('username', 'email', 'occupation', 'atelier', 'is_administrator')
    UserAdmin.fieldsets[1][1]['fields'] += ('is_administrator', 'phone_number', 'atelier', 'occupation')
    list_filter = ('atelier', 'is_staff', 'is_active', 'occupation')
    UserAdmin.add_fieldsets[0][1]['fields'] += ('email', 'atelier', 'occupation')


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

class BaseAdmin(admin.ModelAdmin):
    list_filter = [('created_by',), ('changed_by',)]

    meta_fields = [
        'created_by',
        'created_datetime',
        'changed_by',
        'changed_datetime'
    ]
