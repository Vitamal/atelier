from ievv_opensource.ievv_sms.sms_registry import send_sms

from flexitkt.flexitkt_messages.backends import base


class FlexitSmsMessageSender(base.AbstractMessageSender):
    """
    Send SMS using flexit_sms.
    """
    message_type = 'sms'

    @property
    def send_as(self):
        """
        Get the `send_as` value from `self.message.appspecific_metadata`
        if it exists.
        """
        return self.message.appspecific_metadata \
            .get('send_as', {}) \
            .get('sms', {}) \
            .get('value', None)

    def send_message(self, message_receiver):
        send_sms(phone_number=message_receiver.send_to,
                 message=message_receiver.message.message_content_plain,
                 send_as=self.send_as)
