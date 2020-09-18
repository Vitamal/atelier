from django import test
from django.core.exceptions import ValidationError
from django.test import override_settings
from model_mommy import mommy

from flexitkt.flexitkt_messages.models import BaseMessage, BaseMessageAttachment


class TestBaseMessage(test.TestCase):
    def test_get_message_class_string(self):
        self.assertEqual(BaseMessage.get_message_class_string(), 'flexitkt.flexitkt_messages.models.BaseMessage')

    def test_validate_subject_for_sending_sms(self):
        message = mommy.prepare('flexitkt_messages.BaseMessage', subject='', message_types=['sms'])
        message.validate_subject_for_sending()
        message2 = mommy.prepare('flexitkt_messages.BaseMessage', subject='Test', message_types=['sms'])
        message2.validate_subject_for_sending()

    def test_validate_subject_for_sending_email(self):
        message = mommy.prepare('flexitkt_messages.BaseMessage', subject='', message_types=['email'])
        with self.assertRaises(ValidationError):
            message.validate_subject_for_sending()
        message2 = mommy.prepare('flexitkt_messages.BaseMessage', subject='Test', message_types=['email'])
        message2.validate_subject_for_sending()

    def test_validate_subject_for_sending_email_and_sms(self):
        message = mommy.prepare('flexitkt_messages.BaseMessage', subject='', message_types=['email', 'sms'])
        with self.assertRaises(ValidationError):
            message.validate_subject_for_sending()
        message2 = mommy.prepare('flexitkt_messages.BaseMessage', subject='Test', message_types=['email', 'sms'])
        message2.validate_subject_for_sending()

    def test_validate_message_content_plain_for_sending(self):
        message = mommy.prepare('flexitkt_messages.BaseMessage', message_content_plain='')
        with self.assertRaises(ValidationError):
            message.validate_message_content_plain_for_sending()
        message2 = mommy.prepare('flexitkt_messages.BaseMessage', message_content_plain='Test')
        message2.validate_message_content_plain_for_sending()

    def test_clean_message_content_fields_has_html_but_not_plain(self):
        message = mommy.prepare('flexitkt_messages.BaseMessage',
                                message_content_plain='',
                                message_content_html='<strong>Test</strong>')
        message.clean_message_content_fields()
        self.assertEqual(message.message_content_plain, '**Test**')
        self.assertEqual(message.message_content_html, '<strong>Test</strong>')

    def test_clean_message_content_fields_has_both(self):
        message = mommy.prepare('flexitkt_messages.BaseMessage',
                                message_content_plain='Test plain',
                                message_content_html='<strong>Test</strong>')
        message.clean_message_content_fields()
        self.assertEqual(message.message_content_plain, 'Test plain')
        self.assertEqual(message.message_content_html, '<strong>Test</strong>')

    def test_clean_message_content_fields_has_none(self):
        message = mommy.prepare('flexitkt_messages.BaseMessage',
                                message_content_plain='',
                                message_content_html='')
        message.clean_message_content_fields()
        self.assertEqual(message.message_content_plain, '')
        self.assertEqual(message.message_content_html, '')

    def test_get_email_attachment_ids_sanity(self):
        message = mommy.make('flexitkt_messages.BaseMessage',
                                message_content_plain='',
                                message_content_html='')
        att1 = mommy.make('flexitkt_messages.BaseMessageAttachment', message=message)
        self.assertIn(att1.id, message.get_email_attachment_ids())

    def test_get_email_attachment_links_sanity(self):
        message = mommy.make('flexitkt_messages.BaseMessage',
                                message_content_plain='',
                                message_content_html='')
        att1 = mommy.make('flexitkt_messages.BaseMessageAttachment', message=message,
                          attachment_file_url='https://test.com')
        self.assertEqual(
            'https://test.com',
            message.get_email_attachment_links()[0]['link']
        )


class TestBaseMessageQuerysets(test.TestCase):
    def test_filter_locked_for_edit_status_values(self):
        message_draft = mommy.make('flexitkt_messages.BaseMessage')
        message_queued_for_prepare = mommy.make(
            'flexitkt_messages.BaseMessage', status=BaseMessage.STATUS_CHOICES.QUEUED_FOR_PREPARE.value)
        message_preparing = mommy.make(
            'flexitkt_messages.BaseMessage', status=BaseMessage.STATUS_CHOICES.PREPARING.value)
        message_ready_for_sending = mommy.make(
            'flexitkt_messages.BaseMessage', status=BaseMessage.STATUS_CHOICES.READY_FOR_SENDING.value)
        message_queued_for_sending = mommy.make(
            'flexitkt_messages.BaseMessage', status=BaseMessage.STATUS_CHOICES.QUEUED_FOR_SENDING.value)
        message_sending_in_progress = mommy.make(
            'flexitkt_messages.BaseMessage', status=BaseMessage.STATUS_CHOICES.SENDING_IN_PROGRESS.value)
        message_error = mommy.make(
            'flexitkt_messages.BaseMessage', status=BaseMessage.STATUS_CHOICES.ERROR.value)
        message_sent = mommy.make(
            'flexitkt_messages.BaseMessage', status=BaseMessage.STATUS_CHOICES.SENT.value)
        self.assertNotIn(message_draft, BaseMessage.objects.filter_locked_for_edit_status_values())
        self.assertNotIn(message_queued_for_prepare, BaseMessage.objects.filter_locked_for_edit_status_values())
        self.assertNotIn(message_preparing, BaseMessage.objects.filter_locked_for_edit_status_values())
        self.assertNotIn(message_ready_for_sending, BaseMessage.objects.filter_locked_for_edit_status_values())

        self.assertIn(message_queued_for_sending, BaseMessage.objects.filter_locked_for_edit_status_values())
        self.assertIn(message_sending_in_progress, BaseMessage.objects.filter_locked_for_edit_status_values())
        self.assertIn(message_error, BaseMessage.objects.filter_locked_for_edit_status_values())
        self.assertIn(message_sent, BaseMessage.objects.filter_locked_for_edit_status_values())


class TestBaseMessageAttachmentModel(test.TestCase):

    def test_simple_create_success(self):
        self.assertEqual(BaseMessageAttachment.objects.count(), 0)
        mommy.make('flexitkt_messages.BaseMessageAttachment')
        self.assertEqual(BaseMessageAttachment.objects.count(), 1)

    def test_create_success_with_data(self):
        message = mommy.make('flexitkt_messages.BaseMessage',
                             message_content_plain='',
                             message_content_html='')
        attachment = mommy.make(
            'flexitkt_messages.BaseMessageAttachment',
            message=message,
            attachment_file_url='https://test.com',
            title='title'
        )
        self.assertEqual(BaseMessageAttachment.objects.count(), 1)
        self.assertEqual(attachment.message, message)
        self.assertEqual(attachment.attachment_file_url, 'https://test.com')
        self.assertEqual(attachment.title, 'title')
        self.assertEqual(attachment.requires_login, True)
        self.assertIsNotNone(attachment.unique_identifier)

    def test_delete_success(self):
        attachment = mommy.make('flexitkt_messages.BaseMessageAttachment')
        self.assertEqual(BaseMessageAttachment.objects.count(), 1)
        attachment.delete()
        self.assertEqual(BaseMessageAttachment.objects.count(), 0)
