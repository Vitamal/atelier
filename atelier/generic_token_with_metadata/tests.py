from __future__ import unicode_literals
from datetime import datetime, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from model_mommy import mommy

from atelier.generic_token_with_metadata.models import GenericTokenWithMetadata, generate_token, \
    get_expiration_datetime_for_app


class TestGenericTokenWithMetadata(TestCase):
    def _create_generic_token_with_metadata(self, user, created_datetime=None, expiration_datetime=None,
                                            app='testapp', **kwargs):
        generic_token_with_metadata = GenericTokenWithMetadata.objects.create(
            created_datetime=(created_datetime or timezone.now()),
            expiration_datetime=(expiration_datetime or (timezone.now() + timedelta(days=2))),
            app=app, content_object=user, **kwargs)
        return generic_token_with_metadata

    def test_generate_token(self):
        self.assertEqual(len(generate_token()), 73)
        self.assertNotEqual(generate_token(), generate_token())

    def test_generate(self):
        testuser = mommy.make(get_user_model())
        unique_user_token = GenericTokenWithMetadata.objects.generate(
            content_object=testuser, app='testapp',
            expiration_datetime=get_expiration_datetime_for_app('testapp'))
        self.assertEqual(unique_user_token.content_object, testuser)
        self.assertEqual(unique_user_token.app, 'testapp')
        self.assertEqual(len(unique_user_token.token), 73)

    def test_generate_handle_not_unique(self):
        self._create_generic_token_with_metadata(user=mommy.make(get_user_model()), app='testapp1', token='taken')
        tokens = iter(['taken', 'free'])
        unique_user_token = GenericTokenWithMetadata.objects.generate(
            content_object=mommy.make(get_user_model()), app='testapp2',
            expiration_datetime=get_expiration_datetime_for_app('testapp'), method=lambda **kwargs: next(tokens))
        self.assertEqual(unique_user_token.token, 'free')

    def test_filter_by_content_object(self):
        testobject1 = mommy.make(get_user_model())
        testobject2 = mommy.make(get_user_model())
        generictoken = GenericTokenWithMetadata.objects.generate(
            content_object=testobject1, app='testapp',
            expiration_datetime=get_expiration_datetime_for_app('testapp'))
        self.assertEquals(
            GenericTokenWithMetadata.objects.filter_by_content_object(testobject1).get(),
            generictoken)
        self.assertEquals(GenericTokenWithMetadata.objects.filter_by_content_object(testobject2).count(), 0)

    def test_unsafe_pop(self):
        testuser = mommy.make(get_user_model())
        self._create_generic_token_with_metadata(user=testuser, app='testapp1', token='test-token1')
        self._create_generic_token_with_metadata(user=testuser, app='testapp2', token='test-token2')
        self.assertEquals(GenericTokenWithMetadata.objects.unsafe_pop(
            token='test-token1', app='testapp1').content_object, testuser)
        self.assertEquals(GenericTokenWithMetadata.objects.count(), 1)
        self.assertEquals(GenericTokenWithMetadata.objects.unsafe_pop(
            token='test-token2', app='testapp2').content_object, testuser)
        self.assertEquals(GenericTokenWithMetadata.objects.count(), 0)

    def test_filter_not_expired(self):
        unexpired_generic_token_with_metadata = self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()), token='test-token1',
            expiration_datetime=datetime(2015, 1, 1, 14, 30))
        self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()), token='test-token2',
            expiration_datetime=datetime(2015, 1, 1, 13, 30))

        with mock.patch('atelier.generic_token_with_metadata.models._get_current_datetime',
                        lambda: datetime(2015, 1, 1, 14)):
            self.assertEquals(GenericTokenWithMetadata.objects.filter_not_expired().count(), 1)
            self.assertEquals(GenericTokenWithMetadata.objects.filter_not_expired().first(),
                              unexpired_generic_token_with_metadata)

    def test_filter_not_expired_none(self):
        expired_none_generic_token_with_metadata = self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()), token='test-token1',
            expiration_datetime=None)
        self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()), token='test-token2',
            expiration_datetime=datetime(2015, 1, 1, 13, 30))

        with mock.patch('atelier.generic_token_with_metadata.models._get_current_datetime',
                        lambda: datetime(2015, 1, 1, 14)):
            self.assertEquals(GenericTokenWithMetadata.objects.filter_not_expired().count(), 1)
            self.assertEquals(GenericTokenWithMetadata.objects.filter_not_expired().first(),
                              expired_none_generic_token_with_metadata)

    def test_filter_has_expired(self):
        self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()),
            app='testapp', token='test-token1',
            expiration_datetime=datetime(2015, 1, 1, 14, 30))
        self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()),
            app='testapp', token='test-token2',
            expiration_datetime=None)
        expired_generic_token_with_metadata = self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()),
            app='testapp', token='test-token3',
            expiration_datetime=datetime(2015, 1, 1, 13, 30))

        with mock.patch('atelier.generic_token_with_metadata.models._get_current_datetime',
                        lambda: datetime(2015, 1, 1, 14)):
            self.assertEquals(GenericTokenWithMetadata.objects.filter_has_expired().count(), 1)
            self.assertEquals(GenericTokenWithMetadata.objects.filter_has_expired().first(),
                              expired_generic_token_with_metadata)

    def test_pop_not_expired(self):
        testuser = mommy.make(get_user_model())
        self._create_generic_token_with_metadata(
            user=testuser, token='test-token',
            expiration_datetime=datetime(2015, 1, 1, 14, 30))

        with mock.patch('atelier.generic_token_with_metadata.models._get_current_datetime',
                        lambda: datetime(2015, 1, 1, 14)):
            self.assertEquals(GenericTokenWithMetadata.objects.pop(app='testapp', token='test-token').content_object,
                              testuser)

    def test_pop_expired(self):
        self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()),
            app='testapp', token='test-token',
            expiration_datetime=datetime(2015, 1, 1, 13, 30))

        with mock.patch('atelier.generic_token_with_metadata.models._get_current_datetime',
                        lambda: datetime(2015, 1, 1, 14)):
            with self.assertRaises(GenericTokenWithMetadata.DoesNotExist):
                GenericTokenWithMetadata.objects.pop(app='testapp', token='test-token')

    def test_delete_expired(self):
        unexpired_generic_token_with_metadata = self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()), token='test-token1',
            expiration_datetime=datetime(2015, 1, 1, 14, 30))
        self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()), token='test-token2',
            expiration_datetime=datetime(2015, 1, 1, 13, 30))

        self.assertEquals(GenericTokenWithMetadata.objects.count(), 2)
        with mock.patch('atelier.generic_token_with_metadata.models._get_current_datetime',
                        lambda: datetime(2015, 1, 1, 14)):
            GenericTokenWithMetadata.objects.delete_expired()
        self.assertEquals(GenericTokenWithMetadata.objects.count(), 1)
        self.assertEquals(GenericTokenWithMetadata.objects.first(),
                          unexpired_generic_token_with_metadata)

    def test_delete_expired_management_command(self):
        unexpired_generic_token_with_metadata = self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()), token='test-token1',
            expiration_datetime=datetime(2015, 1, 1, 14, 30))
        self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()), token='test-token2',
            expiration_datetime=datetime(2015, 1, 1, 13, 30))

        self.assertEquals(GenericTokenWithMetadata.objects.count(), 2)
        with mock.patch('atelier.generic_token_with_metadata.models._get_current_datetime',
                        lambda: datetime(2015, 1, 1, 14)):
            call_command('atelier_generic_token_with_metadata_delete_expired')
        self.assertEquals(GenericTokenWithMetadata.objects.count(), 1)
        self.assertEquals(GenericTokenWithMetadata.objects.first(),
                          unexpired_generic_token_with_metadata)

    def test_is_expired(self):
        unexpired_generic_token_with_metadata = self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()), token='test-token1',
            expiration_datetime=datetime(2015, 1, 1, 14, 30))
        expired_generic_token_with_metadata = self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()), token='test-token2',
            expiration_datetime=datetime(2015, 1, 1, 13, 30))

        with mock.patch('atelier.generic_token_with_metadata.models._get_current_datetime',
                        lambda: datetime(2015, 1, 1, 14)):
            self.assertFalse(unexpired_generic_token_with_metadata.is_expired())
            self.assertTrue(expired_generic_token_with_metadata.is_expired())

    def test_is_expired_expiration_datetime_none(self):
        tokenobject = self._create_generic_token_with_metadata(
            user=mommy.make(get_user_model()), token='test-token2',
            expiration_datetime=None)
        self.assertFalse(tokenobject.is_expired())
