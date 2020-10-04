from django.urls import reverse
from django.http import Http404
from django.views.generic.edit import CreateView, UpdateView, ModelFormMixin, ProcessFormView

from ...models import User
from ..user_managment.forms.create_update_user_form import UserCreateForm, UserUpdateForm
from ..view_mixins import UserManagementAccessMixin, RedirectSuccessMixin


class UserCreateUpdateMixin(UserManagementAccessMixin, ModelFormMixin, ProcessFormView):
    model = User
    template_name = 'atelier/user_management/user_create_update.html'
    context_object_name = 'user_to_manage'
    object = None

    def get_success_url(self):
        return reverse('user_management')


class UserCreateView(RedirectSuccessMixin, UserCreateUpdateMixin, CreateView):
    form_class = UserCreateForm

    def get_basic_cancel_url(self):
        return reverse('user_management')

    def form_valid(self, form):
        atelier = self.request.user.atelier
        form.instance.atelier = atelier
        form.save()
        return super().form_valid(form)


class UserUpdateView(UserCreateUpdateMixin, UpdateView):
    pk_url_kwarg = 'user_id'
    form_class = UserUpdateForm

    def get_object(self, queryset=None):
        user_to_manage = super().get_object(queryset)
        if user_to_manage.is_superuser:
            raise Http404()
        return user_to_manage
