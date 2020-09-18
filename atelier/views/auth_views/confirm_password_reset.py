from django.utils.translation import gettext as _
from django.contrib import messages
from django.shortcuts import reverse
from django.views.generic import UpdateView
from django.contrib.contenttypes.models import ContentType
from django.http import Http404

from atelier.models import User
from atelier.views.forms.auth_forms import PasswordForm
from atelier.generic_token_with_metadata.models import GenericTokenWithMetadata, GenericTokenExpiredError


class ConfirmPasswordResetView(UpdateView):
    template_name = 'atelier/one-column-form.html'
    title = _('Reset password')
    model = User
    token_pk_url_kwarg = 'token'
    token = None
    object = None
    form_class = PasswordForm

    def get_object(self, queryset=None):
        if self.object is None:
            self.object = User.objects.get(pk=self.get_token().object_id)
        return self.object

    def get_token(self):
        if self.token is None:
            try:
                self.token = GenericTokenWithMetadata.objects.filter_usable_by_content_type_in_app(
                    content_type=ContentType.objects.get_for_model(User),
                    app=User._meta.app_label).get(token=self.kwargs.get('token'))
            except GenericTokenWithMetadata.DoesNotExist:
                raise Http404()
            except GenericTokenExpiredError:
                raise Http404()
        return self.token

    def get_success_url(self):
        return reverse('login')

    def form_valid(self, form):
        self.token.delete()
        messages.success(self.request, _('Password has been successfully changed.'), extra_tags='alert-success')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['cancel_url'] = reverse('login')
        context['submit_title'] = self.title
        return context
