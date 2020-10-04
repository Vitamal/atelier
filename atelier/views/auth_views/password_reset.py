import datetime

from django.utils import timezone
from django.contrib import messages
from django.shortcuts import reverse
from django.views.generic import FormView
from django.utils.translation import pgettext, gettext as _
from django.utils.html import format_html

from atelier.generic_token_with_metadata.models import GenericTokenWithMetadata
from atelier.atelier_messages.models import SystemMessage
from atelier.views.forms.auth_forms import PasswordResetForm
from atelier.models import User


EXPIRATION_PERIOD_HOURS = 1


class PasswordResetView(FormView):
    template_name = 'atelier/../../templates/base/one-column-form.html'
    form_class = PasswordResetForm
    title = _('Reset password')

    def get_success_url(self):
        return reverse('login')

    @staticmethod
    def get_confirmation_url(user):
        token = GenericTokenWithMetadata.objects.prolong_or_generate(
            app=User._meta.app_label, content_object=user,
            delta_dict={'hours': EXPIRATION_PERIOD_HOURS})
        return reverse('reset_password_confirm', kwargs={'token': token.token})

    def send_email(self, email, user):
        confirmation_url = PasswordResetView.get_confirmation_url(user)
        SystemMessage.objects.send(
            subject=pgettext('Password reset message', 'Confirm password reset'),
            message_content_plain='{message}\n{link}'.format(
                link=confirmation_url,
                message=pgettext(
                    'Password reset message',
                    'Dear %(name)s, You have requested password reset. To confirm, please follow the link:') % {
                    'name': f'{user.first_name} {user.last_name}'}
            ),
            to_email=email,
            message_content_html=format_html(
                '<p>{greeting},</p>'
                '<p>{message}: <a href="{link}">{link_text}</a></p>',
                greeting=pgettext('Password reset message', 'Dear %(name)s') % {
                    'name': f'{user.first_name} {user.last_name}'},
                message=pgettext(
                    'Password reset message html',
                    'You have requested password reset. To confirm, please follow the link'),
                link=confirmation_url,
                link_text=pgettext('Password reset message link text', 'Reset password'),
            ),
        )
        messages.success(self.request, _('Confirmation email has been sent successfully.'), extra_tags='alert-success')

    def form_valid(self, form):
        self.send_email(form.cleaned_data['email'], form.user)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['cancel_url'] = reverse('login')
        context['submit_title'] = self.title
        return context
