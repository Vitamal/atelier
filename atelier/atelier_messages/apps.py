from django.apps import AppConfig
from django.conf import settings


class FlexitktMessagesAppConfig(AppConfig):
    name = 'flexitkt.flexitkt_messages'
    verbose_name = "FlexitKT messages"

    def ready(self):
        # Register linkmobility ievv sms backend
        from ievv_opensource.ievv_sms import sms_registry
        from flexitkt.flexitkt_messages.ievv_sms_backends import linkmobility
        ievv_sms_registry = sms_registry.Registry.get_instance()
        ievv_sms_registry.add(linkmobility.Backend)

        from flexitkt.flexitkt_messages import backend_registry
        from flexitkt.flexitkt_messages.backends import flexit_sms
        from flexitkt.flexitkt_messages import messageclass_registry

        # Here, only DjangoEmailMessageSender was added, but added possibility for registering
        # sending using Mailgun API instead by setting the following setting:
        # FLEXITKT_MESSAGES_EMAIL_BACKEND = 'MAILGUN_API'

        # Check if we should catch all emails in MailTrap except allowed:
        if getattr(settings, 'SEND_TO_ONLY_ALLOWED_ADDRESSES', 'False') == 'True':
            from flexitkt.flexitkt_messages.backends import mailtrap_unless_allowed_then_mailgun_api_email as sender
            backend_registry.Registry.get_instance().add(
                message_sender_class=sender.MailTrapUnlessAllowedElseMailgunApiEmailMessageSender
            )
        else:
            # Check if mailgun api is to be used:
            backend_setting_exists = hasattr(settings, 'FLEXIT_MESSAGES_EMAIL_BACKEND')
            if backend_setting_exists and settings.FLEXIT_MESSAGES_EMAIL_BACKEND == 'MAILGUN_API':
                from flexitkt.flexitkt_messages.backends import mailgun_api_email
                backend_registry.Registry.get_instance().add(
                    message_sender_class=mailgun_api_email.MailgunApiEmailMessageSender
                )
            else:
                # If FLEXIT_MESSAGES_EMAIL_BACKEND does not exist in settings, or if it is
                # different from MAILGUN_API, set the standard django email sender.
                from flexitkt.flexitkt_messages.backends import django_email
                backend_registry.Registry.get_instance().add(
                    message_sender_class=django_email.DjangoEmailMessageSender
                )

        # Add sms message sender to registry
        backend_registry.Registry.get_instance().add(
            message_sender_class=flexit_sms.FlexitSmsMessageSender
        )

        from flexitkt.flexitkt_messages.models import SystemMessage
        messageclass_registry.Registry.get_instance().add(message_class=SystemMessage)
