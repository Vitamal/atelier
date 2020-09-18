import logging
import traceback

from django.utils import timezone

from flexitkt.flexitkt_messages.models import MessageReceiver


class AbstractMessageSender(object):
    """
    An abstract class for sending message. Must be subclassed.
    """
    message_type = None

    def __init__(self, message, message_receivers):
        self.message = message
        self.message_receivers = message_receivers
        self.logger = logging.getLogger(f'{self.__class__.__module__}.{self.__class__.__name__}')

    @classmethod
    def get_message_type(self):
        """
        Get the message type of class.

        You can override this if you need to dynamically determine the message type.

        Raises:
            ValueError: If ``message_type`` is ``None``.
        """
        if self.message_type is None:
            raise ValueError('{}.message_type is None'.format(self.__class__.__name__))
        return self.message_type

    def send_message(self, message_receiver):
        """
        Implement the sending of a message.

        Typical usage::

            def send_message(self, message_receiver):
                # Create email or sms for messagereceiver and send it from ``self.message``.

        """
        raise NotImplementedError()

    def send_messages(self):
        """
        Sends messages to message receivers.

        Do not override this method, override :meth:`~.AbstractMessageSender.send_message` instead.
        """
        for message_receiver in self.message_receivers:
            try:
                self.send_message(message_receiver=message_receiver)
            except Exception as exception:
                self.logger.exception('Sending message to MessageReceiver#%s failed with: %s',
                                      message_receiver.id, exception)
                message_receiver.status = MessageReceiver.STATUS_CHOICES.ERROR.value
                message_receiver.status_data = {
                    'error_message': str(exception),
                    'exception_traceback': traceback.format_exc()
                }
                message_receiver.save()
            else:
                message_receiver.status = MessageReceiver.STATUS_CHOICES.SENT.value
                message_receiver.sent_datetime = timezone.now()
                message_receiver.save()
