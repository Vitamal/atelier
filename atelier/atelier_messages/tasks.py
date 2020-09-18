import time
import traceback
from ievv_opensource.ievv_sms import sms_registry


def prepare_message(message_id, message_class_string, send_when_prepared=False):
    """
    Prepares message for sending.

    Will call the :func:`~.send_message` RQ-task and send the message if
    :obj:`~.flexitkt.flexitkt_messages.models.BaseMessage.requested_send_datetime` is ``None``.

    This task does the following:
        1. Get the message to send. If this fails it means that the message is still locked on the DB-level, or that
           the status has changed(it's already sent or is queued for sending).

        If 1. is OK, then:

            2. The status is set to ``preparing``.
            3. :obj:`~.flexitkt.flexitkt_messages.models.MessageReceiver``s are created for the message.
            4. Status is set to ``queued_for_sending``.

        If ``message.requested_send_datetime`` is ``None`` nothing is done and the status
        is still ``queued_for_sending``, else:

            5. send_message RQ task is called, see docs for that function.

    Note::
        Exceptions raised inside the atomic block for starting the sending process is
        added to the message.status_data.

    Args:
        message_id: A ``BaseMessage`` instance id.
    """
    from django.db import transaction
    from django.conf import settings
    from flexitkt.flexitkt_messages.models import BaseMessage
    from flexitkt.flexitkt_messages import messageclass_registry
    import logging
    logger = logging.getLogger(__name__)

    message_class = messageclass_registry.Registry \
        .get_instance() \
        .get(message_class_string=message_class_string)

    def get_message(status):
        return message_class.objects \
            .select_for_update(skip_locked=True) \
            .filter(status=status) \
            .get(id=message_id)

    def handle_error(message, exception):
        logger.exception('%s: Prepare for BaseMessage#%s crashed with: %s', message_class_string, message.id, exception)
        message.status = BaseMessage.STATUS_CHOICES.ERROR.value
        message.status_data = {
            'error_message': str(exception),
            'exception_traceback': traceback.format_exc()
        }
        message.save()

    with transaction.atomic():
        try:
            message = get_message(status=BaseMessage.STATUS_CHOICES.QUEUED_FOR_PREPARE.value)
        except message_class.DoesNotExist:
            logger.warning('%s: Another task has already started processing the message with ID %s.',
                           message_class_string, message_id)
            return

        try:
            # Set status preparing
            message.status = BaseMessage.STATUS_CHOICES.PREPARING.value
            message.full_clean()
            message.save()
        except Exception as exception:
            handle_error(message=message, exception=exception)
            return

    try:
        with transaction.atomic():
            # Create message receivers
            prepared_message_receivers = message.create_message_receivers()
            message.set_message_recipients_metadata(prepared_message_receivers=prepared_message_receivers)

            # Set status queued_for_sending
            if send_when_prepared:
                message.status = BaseMessage.STATUS_CHOICES.QUEUED_FOR_SENDING.value
                message.full_clean()
                message.save()

            else:
                message.status = BaseMessage.STATUS_CHOICES.READY_FOR_SENDING.value
                message.full_clean()
                message.save()
    except Exception as exception:
        handle_error(message=message, exception=exception)
        return

    # Send message
    if send_when_prepared and message.status == BaseMessage.STATUS_CHOICES.QUEUED_FOR_SENDING.value \
            and message.requested_send_datetime is None:
        if getattr(settings, 'FLEXITKT_MESSAGES_QUEUE_IN_REALTIME', True):
            send_message(message_id=message_id, message_class_string=message_class_string)


def _handle_get_message_failure(logger, message_class, message_class_string, message_id,
                                attempt_number):
    from flexitkt.flexitkt_messages.models import BaseMessage

    try:
        message = message_class.objects.filter(id=message_id)
    except message_class.DoesNotExist:
        logger.error('%s: Trying to send the message with ID %s, but that message does not exist.',
                     message_class_string, message_id)
    else:
        if message.status == BaseMessage.STATUS_CHOICES.READY_FOR_SENDING.value:
            if attempt_number > 10:
                logger.error(
                    '%s: Failed to send the message with ID %s. Attempted to get a lock on it %s times, '
                    'but the status is still %s (must be queued_for_sending to aquire sending lock).',
                    message_class_string, message_id, attempt_number, message.status)
            else:
                logger.warning('%s: Message with ID %s has incorrect status for sending %s '
                               '(must be queued_for_sending). This is attempt %s, so we will try again.',
                               message_class_string, message_id, message.status, attempt_number)
                send_message(message_id=message_id, message_class_string=message_class_string,
                             attempt_number=attempt_number + 1)
        else:
            logger.warning(
                '%s: Another task has probably already started processing/sending the message with ID %s. '
                'Current status is: %s',
                message_class_string, message_id, message.status)


def send_message(message_id, message_class_string, attempt_number=0):
    """
    Sends a message with the appropriate backend.

    This task does the following:
        1. Fetches the message.
        2. Status is set to ``sending_in_progress``
        3. Call backends for each message_type in ``message.message_types``, and sent to `MessageReceiver`s.
           MessageReceiver
    """
    from flexitkt.flexitkt_messages import backend_registry
    from django.db import transaction
    from flexitkt.flexitkt_messages.models import BaseMessage
    from flexitkt.flexitkt_messages import messageclass_registry
    from flexitkt.flexitkt_messages.models import MessageReceiver
    import logging
    logger = logging.getLogger(__name__)

    # The attempt_number and sleep() is here to auto-heal in cases where the database transaction
    # that sets the message status to QUEUED_FOR_SENDING is not committed before the task is
    # started.
    if attempt_number == 0:
        logger.debug('%s: Starting attempt %s for sending message with ID %s.',
                     message_class_string, attempt_number, message_id)
        time.sleep(1)
    else:
        logger.warning('%s: Starting attempt %s for sending message with ID %s.',
                       message_class_string, attempt_number, message_id)
        time.sleep(3)

    message_class = messageclass_registry.Registry \
        .get_instance() \
        .get(message_class_string=message_class_string)

    with transaction.atomic():
        try:
            message = message_class.objects \
                .select_for_update(skip_locked=True) \
                .filter(status=BaseMessage.STATUS_CHOICES.QUEUED_FOR_SENDING.value) \
                .get(id=message_id)
        except message_class.DoesNotExist:
            _handle_get_message_failure(
                logger=logger,
                message_class=message_class,
                message_class_string=message_class_string,
                message_id=message_id,
                attempt_number=attempt_number)
            return

        # Set status sending_in_progress
        message.status = BaseMessage.STATUS_CHOICES.SENDING_IN_PROGRESS.value

        if 'sms' in message.message_types:
            sms_backend = sms_registry.Registry.get_instance().get_backend_class_by_id(backend_id=None)
            message.sms_content_length = sms_backend.get_sms_text_length(message.message_content_plain)
            message.sms_part_count = sms_backend.get_part_count(message.message_content_plain)
        message.save()

    for message_type in message.message_types:
        backend_class = backend_registry.Registry \
            .get_instance() \
            .get(message_type=message_type)
        backend = backend_class(
            message=message,
            message_receivers=message.messagereceiver_set.filter(message_type=message_type))
        backend.send_messages()

    # Set status sent
    if message.messagereceiver_set.filter(status=MessageReceiver.STATUS_CHOICES.ERROR.value).exists():
        error_count = message.messagereceiver_set.filter(status=MessageReceiver.STATUS_CHOICES.ERROR.value).count()
        total_count = message.messagereceiver_set.count()
        if error_count == total_count:
            message.status = BaseMessage.STATUS_CHOICES.ERROR.value
            logger.error('%s: Failed to send BaseMessage#%s to ALL %s recipients.',
                         message_class_string, message.id, total_count)
        else:
            message.status = BaseMessage.STATUS_CHOICES.PARTLY_SENT.value
            logger.warning('%s: Failed to send BaseMessage#%s to %s/%s recipients.',
                           message_class_string, message.id, error_count, total_count)
        message.status_data = {
            'details': f'Failed to send to {error_count}/{total_count} recipients.'
        }
    else:
        message.status = BaseMessage.STATUS_CHOICES.SENT.value
    message.save()
