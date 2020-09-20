from django import test

from atelier.atelier_messages import messageclass_registry
from atelier.atelier_messages.models import BaseMessage


class TestMessageClassRegistry(test.TestCase):
    def test_set_backend(self):
        mockregistry = messageclass_registry.MockableRegistry()
        self.assertEqual(mockregistry.get_pretty_classpath(),
                         'atelier.atelier_messages.messageclass_registry.MockableRegistry')

    def test_get_message_class_not_in_registry(self):
        mockregistry = messageclass_registry.MockableRegistry()
        with self.assertRaisesMessage(ValueError,
                                      'mock_message_class not in '
                                      'atelier.atelier_messages.messageclass_registry.MockableRegistry'):
            mockregistry.get(message_class_string='mock_message_class')

    def test_get_message_class(self):
        mockregistry = messageclass_registry.MockableRegistry()
        mockregistry.add(message_class=BaseMessage)
        self.assertEqual(
            mockregistry.get(message_class_string=BaseMessage.get_message_class_string()),
            BaseMessage)

    def test_contains_not_in_registry(self):
        mockregistry = messageclass_registry.MockableRegistry()
        self.assertNotIn('mock_message_class', mockregistry)

    def test_contains(self):
        mockregistry = messageclass_registry.MockableRegistry()
        mockregistry.add(message_class=BaseMessage)
        self.assertIn(BaseMessage.get_message_class_string(), mockregistry)

    def test_add_duplicate(self):
        mockregistry = messageclass_registry.MockableRegistry()
        mockregistry.add(message_class=BaseMessage)
        with self.assertRaisesMessage(ValueError,
                                      '{} already added to '
                                      'atelier.atelier_messages.messageclass_registry.MockableRegistry'.format(
                                          BaseMessage.get_message_class_string())):
            mockregistry.add(message_class=BaseMessage)

    def test_add(self):
        mockregistry = messageclass_registry.MockableRegistry()
        mockregistry.add(message_class=BaseMessage)
        self.assertIn(BaseMessage.get_message_class_string(), mockregistry)
        self.assertEqual(mockregistry._message_classes[BaseMessage.get_message_class_string()], BaseMessage)

    def test_remove_not_in_registry(self):
        mockregistry = messageclass_registry.MockableRegistry()
        with self.assertRaisesMessage(ValueError, '{} not in '
                                                  'atelier.atelier_messages.messageclass_registry.MockableRegistry'
                .format(BaseMessage.get_message_class_string())):
            mockregistry.remove(message_class_string=BaseMessage.get_message_class_string())

    def test_remove(self):
        mockregistry = messageclass_registry.MockableRegistry()
        mockregistry.add(message_class=BaseMessage)
        self.assertEqual(len(mockregistry._message_classes), 1)
        mockregistry.remove(message_class_string=BaseMessage.get_message_class_string())
        self.assertEqual(len(mockregistry._message_classes), 0)

    def test_iter_empty(self):
        mockregistry = messageclass_registry.MockableRegistry()
        self.assertEqual(list(mockregistry), [])

    def test_iter(self):
        mockregistry = messageclass_registry.MockableRegistry()
        mockregistry.add(message_class=BaseMessage)
        self.assertEqual(list(mockregistry), [BaseMessage])
