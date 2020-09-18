import requests
from django.conf import settings

from flexitkt.flexitkt_messages.backends import base


class MailgunApiEmailMessageSender(base.AbstractMessageSender):
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

    def send_message(self, message_receiver):
        email = self.message.prepare_email(message_receiver=message_receiver)
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
