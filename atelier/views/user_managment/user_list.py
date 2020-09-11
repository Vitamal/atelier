from django.contrib.auth import get_user_model
from django.views.generic import ListView

from atelier.views.view_mixins import AtelierFilterObjectsPreMixin
from atelier.views.view_mixins import UserManagementAccessMixin

USERS_LIMIT_PER_PAGE = 30


class UserListView(AtelierFilterObjectsPreMixin, UserManagementAccessMixin, ListView):
    context_object_name = 'users'
    model = get_user_model()
    template_name = 'atelier/user_list.html'
    paginate_by = USERS_LIMIT_PER_PAGE
    ordering = ['username']
