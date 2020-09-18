from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import pgettext
from django.views.generic import TemplateView

from atelier.atelier_messages.models import SystemMessage


class CodeNotReceivedView(TemplateView):
    template_name = 'atelier/code_not_received.html'
    user = None

    def get_user(self):
        if not self.user:
            self.user = get_user_model().objects.get(id=self.kwargs['user_id'])
        return self.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.get_user()
        context['support_phone_number'] = getattr(settings, 'ATELIER_SUPPORT_PHONE_NUMBER', '0987654321')
        context['login_type'] = self.kwargs.get('type')
        return context

    def send_email_notification(self):
        by_user = f'{self.get_user().get_full_name()} <id: {self.get_user().id}>'
        datetime = timezone.now()
        login_type = self.kwargs.get('type')
        for email in getattr(settings, 'ATELIER_SITE_ADMIN_EMAILS'):
            SystemMessage.objects.send(
                subject=pgettext('Login code not received subject', 'One time login code not received'),
                message_content_plain=pgettext('Login code not received message',
                                               'Hi admin, there was a problem with log in using one time code.'
                                               ' User: %(name)s, on: %(datetime)s, login type: %(type)s') % {
                                          'name': by_user,
                                          'datetime': datetime,
                                          'type': login_type
                                      },
                to_email=email,
                message_content_html=format_html(
                    '<p>{greeting},</p>'
                    '<p>{message}</p>'
                    '<p>{by}</p>'
                    '<p>{on}</p>'
                    '<p>{login_type}</p>',
                    greeting=pgettext('Login code not received greeting', 'Hi, Flexit admin!'),
                    message=pgettext('Login code not received message',
                                     'There was a problem with log in using one time code. See detail below'),
                    by=pgettext('Login code not received by', 'User: %(by)s ') % {
                        'by': by_user
                    },
                    on=pgettext('Login code not received on datetime', 'On: %(on)s ') % {
                        'on': datetime
                    },
                    login_type=pgettext('Login code not received login type', 'Login type: %(type)s ') % {
                        'type': login_type
                    },
                ),
            )

    def get(self, request, *args, **kwargs):
        self.send_email_notification()
        return super().get(request, *args, **kwargs)
