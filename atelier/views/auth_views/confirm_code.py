from django.contrib import messages
from django.contrib.auth import login
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.shortcuts import reverse, redirect
from django.utils.translation import ugettext
from django.views.generic import FormView

from atelier.generic_token_with_metadata.models import GenericTokenWithMetadata, GenericTokenExpiredError
from atelier.models import User
from atelier.views.forms.auth_forms import ConfirmCodeForm


class ConfirmCodeView(FormView):
    template_name = 'atelier/confirm_code.html'
    form_class = ConfirmCodeForm
    _user = None

    def dispatch(self, request, *args, **kwargs):
        if not self.get_usable_tokens().exists():
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('index')

    def get_user(self):
        if self._user is None:
            self._user = User.objects.get(pk=self.kwargs.get('user_id'))
        return self._user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_user()
        context['login_type'] = self.kwargs.get('type')
        context['user'] = user
        if self.kwargs.get('type') == 'mobile':
            context['phone_number'] = user.phone_number
        else:
            context['email'] = user.email
        return context

    def get_usable_tokens(self):
        return GenericTokenWithMetadata.objects.filter_usable_by_content_type_and_id_in_app(
            content_type=ContentType.objects.get_for_model(User), object_id=self.kwargs.get('user_id'),
            app=User._meta.app_label).filter(metadata__type=self.kwargs.get('type'), metadata__attempts__gt=0)

    def form_valid(self, form):
        try:
            self.get_usable_tokens().get_and_check_for_single_use(token=form.data.get('code'))
        except GenericTokenWithMetadata.DoesNotExist:
            token = self.get_usable_tokens().first()
            if token:
                metadata = token.metadata
                if metadata['attempts'] > 0:
                    metadata['attempts'] -= 1
                    self.get_usable_tokens().update(metadata=metadata)
                    messages.warning(
                        self.request,
                        ugettext(f'The code was invalid. You have {metadata["attempts"]} attempts left'),
                        extra_tags='alert-warning'
                    )
                    return redirect(reverse(
                        'confirm_code', kwargs={'user_id': self.kwargs.get('user_id'), 'type': self.kwargs.get('type')}
                    ))
            raise Http404()
        except GenericTokenExpiredError:
            raise Http404()
        login(self.request, self.get_user(), backend='django.contrib.auth.backends.ModelBackend')
        return super().form_valid(form)
