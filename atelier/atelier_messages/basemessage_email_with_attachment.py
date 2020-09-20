from django.template.loader import render_to_string
from atelier.atelier_email.emailutils import AbstractEmail


class BaseMessageEmailWithAttachments(AbstractEmail):
    html_message_template = 'atelier_messages/basemessage_email/basemessage_email_with_attachment.html'
    unsubscribe_message_template = None

    def __init__(self, message, message_receiver, attachment_ids=None, attachment_links=None, email_heading=None, include_header=True, *args, **kwargs):
        self.message = message
        self.attachment_ids = attachment_ids or []
        self.message_receiver = message_receiver
        self.email_heading = email_heading
        self.include_header = include_header
        self.attachment_links = attachment_links or {}
        super().__init__(*args, **kwargs)

    def render_subject(self):
        return self.message.subject

    def get_context_data(self):
        context_data = super().get_context_data()
        context_data['message'] = self.message
        context_data['message_receiver'] = self.message_receiver
        context_data['email_heading'] = self.email_heading
        context_data['include_header'] = self.include_header
        context_data['unsubscribe_message'] = self.render_unsubscribe_message()
        context_data['attachment_links'] = self.attachment_links
        return context_data

    def get_unsubscribe_message_context_data(self):
        return {}

    def render_unsubscribe_message(self):
        if not self.unsubscribe_message_template:
            return ''
        return render_to_string(self.unsubscribe_message_template,
                                self.get_unsubscribe_message_context_data()).strip()
