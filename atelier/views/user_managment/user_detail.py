from django.views.generic import DetailView

from atelier.models import User
from atelier.views.view_mixins import UserManagementAccessMixin


class UserDetailView(UserManagementAccessMixin, DetailView):
    pk_url_kwarg = 'user_id'
    model = User
    template_name = 'atelier/user_detail.html'
    context_object_name = 'user_to_manage'

    def get_queryset(self):
        return super().get_queryset().only('id', 'first_name', 'last_name', 'email', 'username', 'phone_number',
                                           'is_administrator', 'occupation', 'date_joined', 'last_login',
                                           'is_superuser', 'is_staff')
