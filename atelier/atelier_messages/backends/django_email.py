from flexitkt.flexitkt_messages.backends import base


class DjangoEmailMessageSender(base.AbstractMessageSender):
    message_type = 'email'

    def send_message(self, message_receiver):
        email = self.message.prepare_email(message_receiver=message_receiver)
        email.send()
