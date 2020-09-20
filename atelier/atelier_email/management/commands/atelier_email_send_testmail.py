from django.core.management.base import BaseCommand

from atelier.atelier_email import emailutils


class Command(BaseCommand):
    def handle(self, args, **kwargs):
        class DemoEmail(emailutils.AbstractEmail):
            subject_template = 'atelier_email/atelier_email_send_testmail/subject.txt'
            html_message_template = 'atelier_email/atelier_email_send_testmail/html_message.html'

        DemoEmail(recipient='post@appresso.no',
                  extra_context_data={'name': 'Test Name'}).send()
