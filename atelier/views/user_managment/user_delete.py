from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic import DeleteView

from ..view_mixins import UserManagementAccessMixin


class UserDeleteView(UserManagementAccessMixin, DeleteView):
    model = get_user_model()
    pk_url_kwarg = 'user_id'
    success_url = reverse_lazy('user_management')
    template_name = 'atelier/user_management/user_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_name'] = get_user_model().objects.get(id=self.kwargs.get('user_id'))
        return context
