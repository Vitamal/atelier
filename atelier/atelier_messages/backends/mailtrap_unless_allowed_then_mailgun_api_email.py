import requests
from django.conf import settings

from atelier.atelier_messages.backends import base


class MailTrapIsNotConfiguredError(Exception):
    pass


class MailTrapUnlessAllowedElseMailgunApiEmailMessageSender(base.AbstractMessageSender):
    message_type = 'email'

    def get_result_json_id(self, result):
        try:
            result_json = result.json()
            esp_message_id = result_json.get('id')
            if esp_message_id.startswith('<'):
                esp_message_id = esp_message_id[1:]
            if esp_message_id.endswith('>'):
                esp_message_id = esp_message_id[:-1]
            return esp_message_id
        except Exception:
            return None

    def email_address_allowed(self, email_address):
        if email_address in getattr(settings, 'ALLOWED_EMAIL_ADDRESSES', []):
            return True
        if email_address.split('@')[1] in getattr(settings, 'ALLOWED_EMAIL_DOMAINS', []):
            return True
        return False

    def send_message(self, message_receiver):
        email = self.message.prepare_email(message_receiver=message_receiver)
        if self.email_address_allowed(message_receiver.send_to):
            result = requests.post(
                f'{settings.MAILGUN_API_BASE_URL}/messages',
                auth=('api', settings.MAILGUN_API_KEY),
                data={
                    'from': email.get_from_email(),
                    'to': email.get_recipient_list(),
                    'subject': email.render_subject(),
                    'text': email.render_plaintext_message(),
                    'html': email.render_html_message(),
                }
            )
            self.message.esp_ok_status = result.ok
            if not self.message.esp_ok_status:
                self.message.appspecific_metadata['mailgun_sending_error'] = {
                    'about': 'Mailgun API reached, but returned "ok" was False, which means error!',
                    'data': result.json(),
                }
            self.message.esp_message_id = self.get_result_json_id(result)
            self.message.save()
        elif not getattr(settings, 'EMAIL_HOST') == 'smtp.mailtrap.io':
            raise MailTrapIsNotConfiguredError('Please configure MailTrap addon or use another email sending backend')
        else:
            email.send()
