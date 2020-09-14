from django.urls import reverse
from django.http import Http404
from django.views.generic.edit import CreateView, UpdateView, ModelFormMixin, ProcessFormView
from django.utils.translation import gettext

from ...models import User
from ..user_managment.forms.create_update_user_form import UserCreateForm, UserUpdateForm
from ..view_mixins import UserManagementAccessMixin


class UserCreateUpdateMixin(UserManagementAccessMixin, ModelFormMixin, ProcessFormView):
    model = User
    template_name = 'atelier/user_create_update.html'
    context_object_name = 'user_to_manage'
    object = None

    def get_success_url(self):
        return reverse('user_management')


class UserCreateView(UserCreateUpdateMixin, CreateView):

    form_class = UserCreateForm


class UserUpdateView(UserCreateUpdateMixin, UpdateView):

    pk_url_kwarg = 'user_id'
    form_class = UserUpdateForm


    def get_object(self, queryset=None):
        user_to_manage = super().get_object(queryset)
        if user_to_manage.is_superuser:
            raise Http404()
        return user_to_manage
