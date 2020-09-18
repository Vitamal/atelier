from django import test

from flexitkt.flexitkt_messages.backends.base import AbstractMessageSender
from flexitkt.flexitkt_messages import backend_registry


class MockMessageSender(AbstractMessageSender):
    message_type = 'mock_message_sender'

    def send_messages(self):
        pass


class TestBackendRegistry(test.TestCase):
    def test_set_backend(self):
        mockregistry = backend_registry.MockableRegistry()
        self.assertEqual(mockregistry.get_pretty_classpath(),
                         'flexitkt.flexitkt_messages.backend_registry.MockableRegistry')

    def test_get_message_sender_class_not_in_registry(self):
        mockregistry = backend_registry.MockableRegistry()
        with self.assertRaisesMessage(ValueError,
                                      'mock_message_sender not in '
                                      'flexitkt.flexitkt_messages.backend_registry.MockableRegistry'):
            mockregistry.get(message_type='mock_message_sender')

    def test_get_message_sender(self):
        mockregistry = backend_registry.MockableRegistry()
        mockregistry.add(message_sender_class=MockMessageSender)
        self.assertEqual(
            mockregistry.get(message_type='mock_message_sender'),
            MockMessageSender)

    def test_contains_not_in_registry(self):
        mockregistry = backend_registry.MockableRegistry()
        self.assertNotIn('mock_message_sender', mockregistry)

    def test_contains(self):
        mockregistry = backend_registry.MockableRegistry()
        mockregistry.add(message_sender_class=MockMessageSender)
        self.assertIn('mock_message_sender', mockregistry)

    def test_add_duplicate(self):
        mockregistry = backend_registry.MockableRegistry()
        mockregistry.add(message_sender_class=MockMessageSender)
        with self.assertRaisesMessage(ValueError,
                                      'mock_message_sender already added to '
                                      'flexitkt.flexitkt_messages.backend_registry.MockableRegistry'):
            mockregistry.add(message_sender_class=MockMessageSender)

    def test_add(self):
        mockregistry = backend_registry.MockableRegistry()
        mockregistry.add(message_sender_class=MockMessageSender)
        self.assertIn('mock_message_sender', mockregistry._backend_sender_classes)
        self.assertEqual(mockregistry._backend_sender_classes['mock_message_sender'], MockMessageSender)

    def test_remove_not_in_registry(self):
        mockregistry = backend_registry.MockableRegistry()
        with self.assertRaisesMessage(ValueError,
                                      'mock_message_sender not in '
                                      'flexitkt.flexitkt_messages.backend_registry.MockableRegistry'):
            mockregistry.remove(message_type='mock_message_sender')

    def test_remove(self):
        mockregistry = backend_registry.MockableRegistry()
        mockregistry.add(message_sender_class=MockMessageSender)
        self.assertEqual(len(mockregistry._backend_sender_classes), 1)
        mockregistry.remove(message_type='mock_message_sender')
        self.assertEqual(len(mockregistry._backend_sender_classes), 0)

    def test_iter_empty(self):
        mockregistry = backend_registry.MockableRegistry()
        self.assertEqual(list(mockregistry), [])

    def test_iter(self):
        mockregistry = backend_registry.MockableRegistry()
        mockregistry.add(message_sender_class=MockMessageSender)
        self.assertEqual(list(mockregistry), [MockMessageSender])
