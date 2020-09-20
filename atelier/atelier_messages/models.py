import uuid
import warnings

import django_rq
from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import models
from django.db.models import TextField, PositiveIntegerField
from django.utils import timezone
from django.utils.translation import ugettext_lazy
from atelier.atelier_email import emailutils
from ievv_opensource.utils import choices_with_meta

from . import basemessage_email, messageframework_settings
from .tasks import prepare_message, send_message


class BaseMessageQuerySet(models.QuerySet):
    """
    QuerySet for :class:`.BaseMessage`.
    """
    def create_message(self, message_types, subject,
                       virtual_message_receivers,
                       message_content_plain=None,
                       message_content_html=None,
                       requested_send_datetime=None,
                       appspecific_metadata=None,
                       **kwargs):
        """
        Create a :class:`.BaseMessage` (or a subclass when used via the manager
        or a subclass of :class:`.BaseMessage`).

        Args:
            message_types (list): List of message types.
            subject (str):
            virtual_message_receivers:
            message_content_plain:
            message_content_html:
            requested_send_datetime:
            appspecific_metadata:
            **kwargs: Extra kwargs for the message model constructor.
        Returns:

        """
        appspecific_metadata = appspecific_metadata or {}
        message = self.model(
            message_types=message_types,
            subject=subject,
            virtual_message_receivers=virtual_message_receivers,
            message_content_plain=message_content_plain,
            message_content_html=message_content_html,
            requested_send_datetime=requested_send_datetime,
            appspecific_metadata=appspecific_metadata,
            **kwargs
        )
        message.full_clean()
        message.save()
        return message

    def filter_open_for_edit_status_values(self):
        """
        Filter only to include messages that has :obj:`~.BaseMessage.status` status set to one
        of the statuses in :obj:`~.BaseMessage.OPEN_FOR_EDIT_STATUS_VALUES`.

        This means that the message is still in some kind of draft state (e.g.: It
        has not been queued for sending yet).
        """
        return self.filter(status__in=BaseMessage.OPEN_FOR_EDIT_STATUS_VALUES)

    def filter_locked_for_edit_status_values(self):
        """
        Filter only to include messages that has :obj:`~.BaseMessage.status` status set to one
        of the statuses in :obj:`~.BaseMessage.LOCKED_FOR_EDIT_STATUS_VALUES`.

        This means that the sending is progress, or the message has been/tried sent. Filters out
        statuses that means that the message is just drafted or ready, but has not been sent yet.
        """
        return self.filter(status__in=BaseMessage.LOCKED_FOR_EDIT_STATUS_VALUES)

    def filter_in_sending_process(self):
        warnings.warn("Currency.filter_in_sending_process is deprecated. "
                      "Use Currency.handler.filter_in_sending_process instead.",
                      DeprecationWarning)
        return self.filter_locked_for_edit_status_values()

    def user_has_create_message_draft_permission(self, user, **kwargs):
        """
        Must be overridden on the QuerySet for subclasses of
        :class:`.BaseMessage`.

        This is used to determine if the provided ``user`` can
        create a message.

        Args:
            user: A User object. May be ``None``, and may be an
                unauthenticated user. So you need to check that
                when you override this method if it is relevant.
            **kwargs: Extra kwargs. The APIs include the ``request``
                and the ``view`` here.
        """
        raise NotImplementedError(
            'Subclasses must implement the user_has_create_message_draft_permission() '
            'method')

    def filter_is_draft(self):
        """
        Filter to only include messages that has :obj:`~.BaseMessage.status`
        set to `draft` (BaseMessage.STATUS_CHOICES.DRAFT.value).
        """
        return self.filter(status=BaseMessage.STATUS_CHOICES.DRAFT.value)

    def filter_can_update_content(self):
        """
        Filter only messages where editing the content is allowed.

        Editing content is allowed as long as the message is not sent
        and not being prepared for sending. In other words if the
        status is `draft` or `ready_for_sending`.
        """
        return self.filter(status__in=[
            BaseMessage.STATUS_CHOICES.DRAFT.value,
            BaseMessage.STATUS_CHOICES.READY_FOR_SENDING.value,
        ])

    def filter_can_set_status_to_draft(self):
        """
        Filter to only include message that has :obj:`~.BaseMessage.status` set
        to `ready_for_sending` (BaseMessage.STATUS_CHOICES.READY_FOR_SENDING.value).
        """
        return self.filter(status__in=[BaseMessage.STATUS_CHOICES.READY_FOR_SENDING.value])

    def filter_user_has_update_draft_permission(self, user, **kwargs):
        """
        Must be overridden on the QuerySet for subclasses of
        :class:`.BaseMessage`.

        Should only return message objects that the provided ``user`` can
        update. Does not filter by the *draft* status - the :meth:`.filter_is_draft`
        method does that, and that method should always be called on the queryset
        before using this method.

        Args:
            user: A User object. May be ``None``, and may be an
                unauthenticated user. So you need to check that
                when you override this method if it is relevant.
            **kwargs: Extra kwargs. The APIs include the ``request``
                here.
        """
        raise NotImplementedError(
            'Subclasses must implement the filter_user_has_update_draft_permission() '
            'method')

    def filter_user_has_send_permission(self, user, **kwargs):
        """
        Must be overridden on the QuerySet for subclasses of
        :class:`.BaseMessage`.

        Should only return message objects that the provided ``user`` can
        send. The send permission also implies that the user can cancel
        a scheduled message that has not yet been sent.

        Does not filter by the :obj:`.BaseMessage.status` field - code using this
        method is responsible for filtering by the appropriate statuses.

        Args:
            user: A User object. May be ``None``, and may be an
                unauthenticated user. So you need to check that
                when you override this method if it is relevant.
            **kwargs: Extra kwargs. The APIs include the ``request``
                here.
        """
        raise NotImplementedError(
            'Subclasses must implement the filter_user_has_send_permission() '
            'method')

    def filter_user_has_view_permission(self, user, **kwargs):
        """
        Can be overridden on the QuerySet for subclasses of
        :class:`.BaseMessage`.

        Should only return message objects that the provided ``user`` can see.
        Defaults to the same permission required for updating a message.

        Args:
            user: A User object. May be ``None``, and may be an
                unauthenticated user. So you need to check that
                when you override this method if it is relevant.
            **kwargs: Extra kwargs. The APIs include the ``request``
                here.
        """
        return self.filter_user_has_update_draft_permission(user=user, **kwargs)

    def filter_user_has_view_receivers_detail_permission(self, user, **kwargs):
        """
        Can be overridden on the QuerySet for a subclass of :class:`.BaseMessage`.

        Should only return message objects where the user has permission to see
        the receivers detailed information.

        Can be used to check against a message for a receiver.

        Args:
            user: A User object. May be ``None``, and may be an
                unauthenticated user. So you need to check that
                when you override this method if it is relevant.
            **kwargs: Extra kwargs. The APIs include the ``request``
                here.

        """
        return self.filter_user_has_update_draft_permission(user=user, **kwargs)

    def filter_user_has_view_receivers_minimal_permission(self, user, **kwargs):
        """
        Can be overridden on the QuerySet for a subclass of :class:`.BaseMessage`.

        Should only return message objects where the user has permission to see
        the receivers minimal information.

        Can be used to check against a message for a receiver.

        Args:
            user: A User object. May be ``None``, and may be an
                unauthenticated user. So you need to check that
                when you override this method if it is relevant.
            **kwargs: Extra kwargs. The APIs include the ``request``
                here.

        """
        return self.filter_user_has_view_receivers_detail_permission(user=user, **kwargs)


class BaseMessage(models.Model):
    """
    Base class for message models.

    Never used directly. Subclasses must override:

    - :meth:`.prepare_message_receivers`
    - :meth:`.validate_virtual_message_receivers`
    """
    objects = BaseMessageQuerySet.as_manager()

    created_datetime = models.DateTimeField(
        blank=True, null=True, default=timezone.now
    )

    #: Choices for :obj:`~.BaseMessage.status`.
    #:
    #: - ``draft``: The message is in the draft state. This means that
    #:   it has not been queued for sending yet, and can still be changed.
    #: - ``queued_for_prepare``: Queued for prepare. This means that
    #:   the message is not yet *prepared*, and a background task
    #:   will soon process it and create :class:`.MessageReceiver` objects.
    #: - ``preparing``: The message is being prepared for sending. This
    #:   means that a background task is creating :class:`.MessageReceiver`
    #:   objects for the message.
    #: - ``queued_for_sending``: Queued for sending.
    #: - ``sending_in_progress``: A background task is sending the message.
    #: - ``error``: Something went wrong. Details in :obj:`~.BaseMessage.status_data`.
    #: - ``sent``: The message has been sent without any errors.
    STATUS_CHOICES = choices_with_meta.ChoicesWithMeta(
        choices_with_meta.Choice(value='draft',
                                 label=ugettext_lazy('Draft')),
        choices_with_meta.Choice(value='queued_for_prepare',
                                 label=ugettext_lazy('In prepare for sending queue')),
        choices_with_meta.Choice(value='preparing',
                                 label=ugettext_lazy('Preparing for sending'),
                                 description=ugettext_lazy('Building the list of actual users to send to.')),
        choices_with_meta.Choice(value='ready_for_sending',
                                 label=ugettext_lazy('Ready for sending'),
                                 description=ugettext_lazy('Message is ready to be sent.')),
        choices_with_meta.Choice(value='queued_for_sending',
                                 label=ugettext_lazy('Queued for sending')),
        choices_with_meta.Choice(value='sending_in_progress',
                                 label=ugettext_lazy('Sending')),
        choices_with_meta.Choice(value='error',
                                 label=ugettext_lazy('Error')),
        choices_with_meta.Choice(value='partly_sent',
                                 label=ugettext_lazy('Failed to send to some of the recipients')),
        choices_with_meta.Choice(value='sent',
                                 label=ugettext_lazy('Sent'))
    )

    #: :obj:`~.BaseMessage.status` values when the message content is editable.
    #: E.g.: message text, subject, etc. can be edited.
    #:
    #: WARNING: :obj:`~.BaseMessage.virtual_message_receivers` should normally not be edited unless the status is
    #: `draft` unless you know what you are doing (you will need to re-prepare the message after editing
    #: virtual_message_receivers)
    OPEN_FOR_EDIT_STATUS_VALUES = (
        STATUS_CHOICES.DRAFT.value,
        STATUS_CHOICES.QUEUED_FOR_PREPARE.value,
        STATUS_CHOICES.PREPARING.value,
        STATUS_CHOICES.READY_FOR_SENDING.value,
    )

    #: :obj:`~.BaseMessage.status` values when the message is being sent, or sending is complete.
    #:
    #: WARNING: **Never** edit anything on the message when it has one of these statuses. The only
    #: exception from this is that the tasks that change the status and status_data will edit the message.
    LOCKED_FOR_EDIT_STATUS_VALUES = (
        STATUS_CHOICES.QUEUED_FOR_SENDING.value,
        STATUS_CHOICES.SENDING_IN_PROGRESS.value,
        STATUS_CHOICES.ERROR.value,
        STATUS_CHOICES.PARTLY_SENT.value,
        STATUS_CHOICES.SENT.value,
    )

    #: Status of the message. Defaults to ``"draft"``.
    #:
    #: Never set this when creating
    #: a message - updating status is done automatically by
    #: the various RQ tasks and utilities provided by the framework.
    #:
    #: Valid values for this is defined in :obj:`~.BaseMessage.STATUS_CHOICES`.
    status = models.CharField(
        max_length=30,
        db_index=True,
        choices=STATUS_CHOICES.iter_as_django_choices_short(),
        default=STATUS_CHOICES.DRAFT.value
    )

    #: Extra data for the :obj:`~.BaseMessage.status` as JSON. Typically used to
    #: save responses from the APIs used to send the message, especially
    #: error responses.
    status_data = JSONField(null=False, blank=True, default=dict)

    #: ESP (Email Service Provider) specific message id. Set when using API to send message and when
    #: webhooks can be used for getting sending status also from the ESP.
    esp_message_id = models.CharField(
        max_length=255,
        blank=True, null=True, default=None,
        unique=True,
        help_text='Email service provider message id'
    )

    #: ESP (Email Service Provider) status (the one returned from the ESP when
    #: sending email through API. If none, not relevant, if
    #: True, then ESP received with no errors, else False.
    esp_ok_status = models.NullBooleanField(null=True, blank=True, default=None)

    #: ArrayField (python list) with the types for this message.
    #: Examples:
    #: - ``['email']`` - Send as email only
    #: - ``['sms']`` - Send as SMS only
    #: - ``['email', 'sms']`` - Send as both email and SMS
    message_types = ArrayField(
        models.CharField(max_length=30),
        blank=False, null=False)

    #: The subject of the message
    subject = models.CharField(max_length=255, null=False, blank=True, default='')

    #: Message content plain text.
    #:
    #: Required. When sending a message, and you only have a HTML message.
    #: The :meth:`.clean_message_content_fields` method automatically sets this from
    #: :obj:`~.BaseMessage.message_content_html` if this field is blank and ``message_content_html``
    #: is not blank.
    message_content_plain = TextField(null=False, blank=True, default='')

    #: Message content length for sms
    #:
    #: The actual sms content length since sms use different encoding
    sms_content_length = PositiveIntegerField(null=True, default=None, blank=True)

    #: Message part count
    #:
    #: Sms messages might be divided into multiple sms messages which is actually sent
    sms_part_count = PositiveIntegerField(null=True, default=None, blank=True)

    #: Message content HTML.
    #: Optional, but normally used when sending an email.
    #:
    #: Note that you normally do not include header/banner, footer,
    #: signature etc. in this, that is normally handled in :meth:`~.BaseMessage.prepare_email`.
    #: If you want users to specify data to put in banner/footer/signature
    #: etc. you normally want to use :obj:`~.BaseMessage.appspecific_metadata`
    #: or custom model fields on your BaseMessage subclass.
    message_content_html = TextField(null=False, blank=True, default='')

    #: Requested datetime to send the message. If this is ``None``, the message
    #: is scheduled for sending as soon as .
    requested_send_datetime = models.DateTimeField(blank=True, null=True)

    #: The user that sent the message.
    #: Not required, but some subclasses may require it. In any case,
    #: you normally want to save the user who sent a message as long as
    #: you have one.
    sent_by = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                null=True, blank=True, on_delete=models.SET_NULL)

    #: The user that created the message.
    #: Not required, but some subclasses may require it. In any case,
    #: you normally want to save the user who sent a message as long as
    #: you have one.
    created_by = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                   on_delete=models.SET_NULL,
                                   related_name='created_messages',
                                   null=True, blank=True, default=None)

    #: A JSON object that specifies the message receivers.
    #:
    #: You never create :class:`.MessageReceiver` objects. Instead,
    #: you specify the receivers in ``virtual_message_receivers``,
    #: and the :meth:`.create_message_receivers` method creates
    #: the message receivers.
    #:
    #: This field is validated via :meth:`.validate_virtual_message_receivers`,
    #: which is called from :meth:`.clean`.
    virtual_message_receivers = JSONField(null=False, blank=True, default=dict)

    #: An optional JSON object where you can put application specific metadata.
    appspecific_metadata = JSONField(null=False, blank=True, default=dict)

    #: The datetime when this object was anonymized
    anonymized_datetime = models.DateTimeField(null=True, blank=True, default=None)

    @classmethod
    def get_message_class_string(cls):
        """
        A unique identifier for this class used in registries.
        """
        return '{}.{}'.format(cls.__module__, cls.__name__)

    def queue_for_prepare(self, send_when_prepared=False, sent_by=None):
        if self.status != self.STATUS_CHOICES.DRAFT.value:
            raise ValueError(f'Can only call queue_for_prepare on messages with '
                             f'status={self.STATUS_CHOICES.DRAFT.value!r}. Current status: {self.status!r}.')
        self.sent_by = sent_by
        self.status = self.STATUS_CHOICES.QUEUED_FOR_PREPARE.value
        self.full_clean()
        self.save()

        # Prepare sending with RQ task.
        if getattr(settings, 'ATELIER_MESSAGES_QUEUE_IN_REALTIME', True):
            django_rq.get_queue(messageframework_settings.get_rq_queue_name())\
                .enqueue(prepare_message,
                         message_id=self.id,
                         message_class_string=self.__class__.get_message_class_string(),
                         send_when_prepared=send_when_prepared)

    def queue_for_sending(self, sent_by=None):
        """
        Sets :obj:`~.BaseMessage.sent_by` to the provided ``sent_by`` user,
        updates the :obj:`~.BaseMessage.status` to ``queued_for_prepare``
        (I.E.: ``BaseMessage.STATUS_CHOICES.QUEUED_FOR_PREPARE.value``),
        and start an RQ task that prepares the message for sending.

        If :obj:`~.BaseMessage.requested_send_datetime` is ``None``, the RQ
        task that prepares the message for sending will start another RQ
        task that actually sends the message. If it is not ``None``,
        the message will end up with :obj:`~.BaseMessage.status` set to ``"queued"``,
        and some background task, cronjob, etc. will have to pick it up
        and send it when the time is right.

        Args:
            sent_by: The User who is sending the message - optional,
                but normally used unless you are sending without a user
                (authenticating in some other way).
        """
        if self.status == self.STATUS_CHOICES.DRAFT.value:
            self.queue_for_prepare(send_when_prepared=True, sent_by=sent_by)
        elif self.status == self.STATUS_CHOICES.READY_FOR_SENDING.value:
            self.status = self.STATUS_CHOICES.QUEUED_FOR_SENDING.value
            self.clean()
            self.save()
            if getattr(settings, 'ATELIER_MESSAGES_QUEUE_IN_REALTIME', True):
                django_rq.get_queue(messageframework_settings.get_rq_queue_name())\
                    .enqueue(send_message,
                             message_id=self.id,
                             message_class_string=self.__class__.get_message_class_string())
        else:
            raise ValueError(f'Can only call queue_for_sending if status is one of: '
                             f'{self.STATUS_CHOICES.READY_FOR_SENDING.value!r} or '
                             f'{self.STATUS_CHOICES.DRAFT.value!r}. Current status is: {self.status!r}.')

    def prepare_message_receivers(self):
        """
        Prepare :class:`.MessageReceiver` objects for :meth:`.create_message_receivers`.

        By _prepare_, we mean to make the MessageReceiver objects, but not save
        them to the database. Saving is handled with a bulk create in
        :meth:`.create_message_receivers`.

        Must return a list of :class:`.MessageReceiver` objects, or a
        generator that yields lists of :class:`.MessageReceiver` objects.

        Must be overridden in subclasses.
        """
        raise NotImplementedError()

    def _create_message_receivers_from_list(self, message_receiver_list):
        MessageReceiver.objects.bulk_create(message_receiver_list)

    def set_message_recipients_metadata(self, prepared_message_receivers):
        """
        Set extra metadata about the recipients.

        This is called during the background tasks that create message receivers. It is called
        after :meth:`.create_message_receivers`, and the input to this method is the output from
        create_message_receivers().

        Typical use case is storing info about the users that did not end up as message receivers.

        Do NOT save in this method, just set things - typically in `appspecific_metadata`.

        Args:
            prepared_message_receivers: The response from :meth:`.prepare_message_receivers`
        """

    def create_message_receivers(self):
        """
        Create :obj:`.MessageReceiver` objects for this message
        from :obj:`~.BaseMessage.virtual_message_receivers`.

        You never call this directly unless you are making background
        task for preparing a message for sending.

        Returns:
            What was returned from :meth:`.prepare_message_receivers`.
        """
        message_receivers = self.prepare_message_receivers()
        if isinstance(message_receivers, list):
            self._create_message_receivers_from_list(message_receivers)
        else:
            for message_receiver_list in message_receivers:
                self._create_message_receivers_from_list(message_receiver_list)

        return message_receivers

    def validate_virtual_message_receivers(self):
        """
        Validate :obj:`~.BaseMessage.virtual_message_receivers`.

        Here you should just validate the structure of the field,
        but you should allow it to be empty. Validate required
        attributes in :meth:`.validate_virtual_message_receivers_for_sending`.

        Does nothing by default.
        """

    def validate_virtual_message_receivers_for_sending(self):
        """
        Validate :obj:`~.BaseMessage.virtual_message_receivers`
        when the :obj:`~.BaseMessage.status` is
        not ``draft`` (I.E.: ``BaseMessage.STATUS_CHOICES.QUEUED_FOR_PREPARE.value``).

        By default, this just validates that :obj:`~.BaseMessage.virtual_message_receivers`
        is not blank.
        """
        return self.validate_not_blank('virtual_message_receivers', self.virtual_message_receivers)

    def get_email_class(self, message_receiver):
        """
        Get the :class:`django_cradmin.apps.cradmin_email.emailutils.AbstractEmail` subclass
        to use for sending emails.

        Args:
            message_receiver (.MessageReceiver): The message reciever that the email will be sent to.
                Normally ignored in implementations of this method, but you can use
                it if you want to use different email classes for different recipients.

        Returns:
            django_cradmin.apps.cradmin_email.emailutils.AbstractEmail: A subclass of AbstractEmail from
                django_cradmin. A class, not an object/instance of the class!
        """
        raise NotImplementedError()

    def get_email_kwargs(self, message_receiver):
        """
        Get kwargs for the constructor of the class returned by :meth:`.get_email_class`.

        Args:
            message_receiver (.MessageReceiver): The message reciever that the email will be sent to.

        Returns:
            dict: Kwargs
        """
        return {
            'message': self,
            'message_receiver': message_receiver,
            'recipient': message_receiver.send_to,
            'extra_context_data': {'attachment_links': self.get_email_attachment_links()}
        }

    def get_email_attachment_links(self):
        def get_url_obj(att):
            return {
                'title': att.title,
                'link': att.attachment_file_url
            }
        return [get_url_obj(attachment) for attachment in BaseMessageAttachment.objects.filter(message=self)]

    def get_email_attachment_ids(self):
        return [attachment.id for attachment in BaseMessageAttachment.objects.filter(message=self)]

    def prepare_email(self, message_receiver):
        """
        Prepare a :class:`django_cradmin.apps.cradmin_email.emailutils.AbstractEmail`
        object that can be used to send this message as an email.

        Can be overridden in subclasses, but you normally just want
        to override :meth:`.get_email_class`, and perhaps :meth:`.get_email_kwargs`.
        """
        return self.get_email_class(message_receiver=message_receiver)(
            **self.get_email_kwargs(message_receiver=message_receiver))

    def validate_not_blank(self, fieldname, value):
        if not value:
            raise ValidationError({
                fieldname: models.Field.default_error_messages['blank']
            })

    def clean_message_content_fields(self):
        """
        Clean :obj:`~.BaseMessage.message_content_plain` and :obj:`~.BaseMessage.message_content_html`.

        Defaults to setting :obj:`~.BaseMessage.message_content_plain` from
        :obj:`~.BaseMessage.message_content_html` using
        :meth:`django_cradmin.apps.cradmin_email.emailutils.convert_html_to_plaintext` if
        message_content_plain is blank and message_content_html is not blank.
        """
        if self.message_content_html and not self.message_content_plain:
            self.message_content_plain = emailutils.convert_html_to_plaintext(self.message_content_html).strip()

    def validate_subject_for_sending(self):
        """
        Validate :obj:`~.BaseMessage.subject` for sending.

        By default this just makes subject required if ``email`` is in
        :obj:`.~BaseMessage.message_types`.
        """
        if 'email' in self.message_types:
            self.validate_not_blank('subject', self.subject)

    def validate_message_content_plain_for_sending(self):
        """
        Validate :obj:`~.BaseMessage.message_content_plain` for sending.

        Required the field to not be blank by default
        """
        self.validate_not_blank('message_content_plain', self.message_content_plain)

    def validate_message_content_html_for_sending(self):
        """
        Validate :obj:`~.BaseMessage.message_content_html` for sending.

        Does nothing by default.
        """

    def validate_for_sending(self):
        """
        Called by :meth:`.clean` as long as  :obj:`~.BaseMessage.status` is
        not ``draft`` (I.E.: ``BaseMessage.STATUS_CHOICES.QUEUED_FOR_PREPARE.value``).

        You can override this to validate what fields and values are required
        when the message status is not ``draft``.

        Do not validate :obj:`~.BaseMessage.virtual_message_receivers` here.
        That should be done in :meth:`.validate_virtual_message_receivers_for_sending`,
        which is called after this method in :meth:`.clean`.

        By default we call:
        - :meth:`validate_subject_for_sending`
        - :meth:`validate_message_content_plain_for_sending`
        - :meth:`validate_message_content_html_for_sending`
        - :meth:`validate_virtual_message_receivers_for_sending`

        so if you want to keep this behavior, remember to call super()
        when overriding this method.
        """
        self.validate_subject_for_sending()
        self.validate_message_content_plain_for_sending()
        self.validate_message_content_html_for_sending()
        self.validate_virtual_message_receivers_for_sending()

    def clean(self):
        """
        Calls :meth:`.validate_virtual_message_receivers`.

        If you override this in subclasses, make sure you call ``super().clean()``.
        """
        self.subject = self.subject.strip()
        self.message_content_plain = self.message_content_plain.strip()
        self.clean_message_content_fields()
        self.validate_virtual_message_receivers()
        if self.status not in [self.STATUS_CHOICES.DRAFT.value,
                               self.STATUS_CHOICES.QUEUED_FOR_PREPARE.value,
                               self.STATUS_CHOICES.PREPARING.value,
                               self.STATUS_CHOICES.READY_FOR_SENDING.value]:
            self.validate_for_sending()

    def set_status_to_draft(self):
        """
        Set the status of the message to `draft`.
        """
        self.status = self.STATUS_CHOICES.DRAFT.value
        self.save()

    @property
    def is_draft(self):
        """
        Returns ``True`` if the :obj:`~.BaseMessage.status` if ``draft``
        (I.E.: ``BaseMessage.STATUS_CHOICES.DRAFT.value``).
        """
        return self.status == self.STATUS_CHOICES.DRAFT.value

    @property
    def status_label(self):
        return self.STATUS_CHOICES[self.status].label

    @property
    def status_description(self):
        return self.STATUS_CHOICES[self.status].description

    def __str__(self):
        label = self.subject
        if not label:
            label = f'#{self.id}'
        return f'#{self.id} {label} ({self.status_label})'


class MessageReceiver(models.Model):
    #: Choices for the :obj:`.MessageReceiver.status` field.
    #:
    #: - ``not_sent``: The MessageReceiver has just been created, but not sent yet.
    #: - ``error``: There is some error with this message. Details about the error(s)
    #:   is available in :obj:`.status_data`.
    #: - ``sent``: Sent to the backend. We do not know if it was successful or
    #:   not yet when we have this status (E.g.: We do not know if the message has been received, but
    #:   we are waiting for an update that tells us if it was).
    #:   Backends that do not support reporting if messages was sent successfully
    #:   or not will only use this status, not the ``received`` status.
    #: - ``received``: If we have this status, we are sure the message has been received.
    #:   Only available when the backend has some way to ensure that a message is received.
    #:   This is typically something that is updated some time after (sometimes many days after)
    #:   the message has been sent.
    STATUS_CHOICES = choices_with_meta.ChoicesWithMeta(
        choices_with_meta.Choice(value='not_sent',
                                 label=ugettext_lazy('Not sent')),
        choices_with_meta.Choice(value='error',
                                 label=ugettext_lazy('Error')),
        choices_with_meta.Choice(value='sent',
                                 label=ugettext_lazy('Sent')),
        choices_with_meta.Choice(value='received',
                                 label=ugettext_lazy('Received')),
    )

    #: The datetime when this object was anonymized
    anonymized_datetime = models.DateTimeField(null=True, blank=True, default=None)

    #: The :class:`.Message` this MessageReceiver belongs too.
    message = models.ForeignKey(to=BaseMessage, on_delete=models.CASCADE)

    #: The message type.
    #: Will always be one of the message types in the :obj:`.BaseMessage.message_types`
    #: list of the :obj:`~.MessageReceiver.message`.
    message_type = models.CharField(max_length=30, db_index=True)

    #: The receiver. For email, this is the receiver email, for SMS this is the
    #: receiver phone number, and so on.
    send_to = models.CharField(max_length=255)

    #: Extra metadata for the receiver. Typically used if :obj:`~.MessageReceiver.send_to`
    #: is not enough (not enough with just a CharField).
    #: Can also be used to add more metadata about the receiver, such as their name.
    send_to_metadata = JSONField(null=False, blank=True, default=dict)

    #: The User to send this to. Only here as metadata to make it
    #: possible to do things like have a view where users can view
    #: messages sent to them. Not required, and not used to actually
    #: send the message (we use :obj:`~.MessageReceiver.send_to` and :obj:`~.MessageReceiver.send_to_metadata`
    #: for that).
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                             null=True, blank=True, on_delete=models.SET_NULL)

    #: The datetime the message was sent.
    sent_datetime = models.DateTimeField(null=True, blank=True)

    #: The status of the message.
    #: Must be one of the choices defined in :obj:`~.MessageReceiver.STATUS_CHOICES`.
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES.iter_as_django_choices_short(),
        default=STATUS_CHOICES.NOT_SENT.value
    )

    #: Extra data for the :obj:`~.MessageReceiver.status` as JSON. Typically used to
    #: save responses from the APIs used to send the message, especially
    #: error responses.
    status_data = JSONField(null=False, blank=True, default=dict)

    @property
    def status_label(self):
        return self.STATUS_CHOICES[self.status].label

    @property
    def status_description(self):
        return self.STATUS_CHOICES[self.status].description


class SystemMessageQuerySet(BaseMessageQuerySet):
    """
    QuerySet for :class:`.SystemMessage`.
    """
    def _is_superuser(self, user):
        if not user:
            return False
        if not user.is_authenticated:
            return False
        return user.is_superuser

    def user_has_create_message_draft_permission(self, user, **kwargs):
        return self._is_superuser(user=user)

    def filter_user_has_update_draft_permission(self, user, **kwargs):
        if self._is_superuser(user=user):
            return self.all()
        return self.none()

    def filter_user_has_send_permission(self, user, **kwargs):
        if self._is_superuser(user=user):
            return self.all()
        return self.none()

    def send(self, subject, message_content_html, to_email=None, to_phone_number=None,
             message_content_plain=None, send_both=False, ignore_no_recipient=False,
             email_heading=None):
        """
        Convenience method / shortcut for creating a :class:`.SystemMessage`, and
        queuing it for sending.

        Example::

            SystemMessage.objects.send(
                subject='Test',
                message_content_html=format_html('Hello <b>Cruel</b> {what}', what='World'),
                to_email='test@example.com',
                to_phone_number='12345678')

        Args:
            subject (str): The email subject.
            message_content_html (str): The message content HTML.
            to_email (str): The recipient email address. Optional.
            to_phone_number: The recipient email address. Optional.
            message_content_plain (str): The plain message content.
                Generated from ``message_content_html`` when it is not
                provided.
            send_both (boolean): Send both SMS and email. Then this is ``False``
                (the default), we only send SMS if ``to_email`` is blank/None.
            ignore_no_recipient (boolean): If this is ``True`` we
                just return ``None`` if both ``to_email`` and ``to_sms`` is
                blank/None.
            email_heading (str): The heading of the email.

        Returns:
            .SystemMessage: The system message that was created and queued for sending.
            May also return ``None`` if the ``ignore_no_recipient`` argument is ``True``
            and no email or phone number was provided.
        """
        if not (to_email or to_phone_number):
            if ignore_no_recipient:
                return None
            else:
                raise ValueError('Must supply at least one of to_email and to_phone_number. '
                                 'To disable this check, use ignore_no_recipient=True.')
        message_types = []
        if to_email:
            message_types.append('email')
        if to_phone_number:
            message_types.append('sms')
        if not send_both and len(message_types) == 2:
            message_types = ['email']
        message = self.create_message(
            subject=subject,
            email_heading=email_heading or '',
            message_types=message_types,
            message_content_html=message_content_html,
            message_content_plain=message_content_plain,
            virtual_message_receivers={
                'to_email': to_email,
                'to_phone_number': to_phone_number
            }
        )
        message.queue_for_sending()
        return message


class SystemMessage(BaseMessage):
    """
    A ready to use system message model.

    This is intended to be used instead of ``send_email(...)`` etc.
    via :meth:`.SystemMessageQuerySet.send`.

    You can create a proxy subclass of this to adjust the
    email templates etc.

    The permissions for this message type is to only allow
    superusers to view, create and update it.
    """
    objects = SystemMessageQuerySet.as_manager()
    email_heading = models.TextField(null=False, blank=True, default='')

    @classmethod
    def get_message_class_string(cls):
        """
        A unique identifier for this class used in registries.
        """
        return 'SystemMessage'

    @property
    def to_email(self):
        return self.virtual_message_receivers.get('to_email')

    @property
    def to_phone_number(self):
        return self.virtual_message_receivers.get('to_phone_number')

    def validate_virtual_message_receivers(self):
        if not isinstance(self.virtual_message_receivers, dict):
            raise ValidationError('virtual_message_receivers must be a dict.')
        if self.to_email:
            EmailValidator(message='Invalid email')(self.to_email)

    def validate_virtual_message_receivers_for_sending(self):
        if 'email' in self.message_types and not self.to_email:
            raise ValidationError('to_email is required when sending an email message')
        if 'sms' in self.message_types and not self.to_phone_number:
            raise ValidationError('to_phone_number is required when sending an SMS message')

    def prepare_message_receivers(self):
        message_receiver_list = []
        if 'email' in self.message_types:
            message_receiver_list.append(
                MessageReceiver(send_to=self.to_email, message=self, message_type='email'))
        if 'sms' in self.message_types:
            message_receiver_list.append(
                MessageReceiver(send_to=self.to_phone_number, message=self, message_type='sms'))
        return message_receiver_list

    def get_email_class(self, *args, **kwargs):
        class SystemEmail(basemessage_email.BaseMessageEmail):
            pass
        return SystemEmail

    def get_email_kwargs(self, message_receiver):
        kwargs = super().get_email_kwargs(message_receiver=message_receiver)
        kwargs['email_heading'] = self.email_heading
        return kwargs


class BaseMessageAttachmentQuerySet(models.QuerySet):
    """
    QuerySet and manager for :class:`.BaseMessageAttachment`.
    """

    def _make_unique_identifier(self):
        uuids = '{uuid_a}{uuid_b}'.format(
            uuid_a=uuid.uuid4(),
            uuid_b=uuid.uuid4()
        ).replace('-', '')
        unique_identifier = '{uuids}'.format(
            uuids=uuids
        )
        if BaseMessageAttachment.objects.filter(unique_identifier=unique_identifier).exists():
            return self._make_unique_identifier()
        else:
            return unique_identifier

    def make_unique_identifier(self):
        """
        Make the unique_identifier.

        We use ``<uuid.uuid4()>_<uuid.uuid4()>``. This
        means that we make a very hard to guess and guaranteed unique
        identifier.
        """
        return self._make_unique_identifier()


class BaseMessageAttachment(models.Model):
    """
    A model for storing attachment file and
    link it to the message it belongs to.
    """
    objects = BaseMessageAttachmentQuerySet.as_manager()

    # BaseMessage instance this file belongs to
    message = models.ForeignKey(
        to=BaseMessage,
        related_name='attachments',
        on_delete=models.CASCADE
    )

    # A url of the attachment file
    attachment_file_url = models.URLField(
    )

    unique_identifier = models.CharField(
        max_length=1000,
        unique=True,
        editable=False,
        blank=True, null=False
    )

    requires_login = models.BooleanField(default=True)

    title = models.CharField(
        max_length=255,
        null=False,
        blank=True,
        default=''
    )

    def clean(self):
        if not self.unique_identifier:
            if self.id is None:
                self.unique_identifier = BaseMessageAttachment.objects.make_unique_identifier()
            else:
                raise ValidationError({
                    'unique_identifier': 'This field is required.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
