from ievv_opensource.utils.singleton import Singleton


class Registry(Singleton):
    """
    A registry used for the different subclasses of :class:`~.flexitkt.flexitkt_messages.models.BaseMessage`.

    We need some way of fetching the correct model-class to work on since we need to pass down
    `BaseMessage`-subclass entry IDs to the RQ-tasks. This registry solved this problem.

    The key used to get and remove `BaseMessage` subclasses from the registry is automatically generated by
    the class method :func:`~.flexitkt.flexitkt_messages.models.BaseMessage.get_message_class_string`
    """
    def __init__(self):
        super().__init__()
        self._message_classes = {}

    def __contains__(self, message_class_string):
        """
        Implement "in"-operator support for ``Registry._message_classes``.
        """
        return message_class_string in self._message_classes

    def __iter__(self):
        """
        Iterate over the registry yielding
        subclasses of :class:`.flexitkt.flexitkt_messages.models.BaseMessage`.
        """
        return iter(self._message_classes.values())

    def get_pretty_classpath(self):
        """
        Prettified string of the registry path.
        """
        return '{}.{}'.format(self.__module__, self.__class__.__name__)

    def get(self, message_class_string):
        """
        Get a subclass of :class:`.flexitkt.flexitkt_messages.models.BaseMessage` stored in the
        registry by the ``message_class_string``

        Args:
            message_class_string (str): A unique string identifier of a
                :class:`.flexitkt.flexitkt_messages.BaseMessage` subclass.
        """
        if message_class_string not in self:
            raise ValueError('{} not in {}'.format(message_class_string, self.get_pretty_classpath()))
        return self._message_classes[message_class_string]

    def add(self, message_class):
        """
        Add the provided ``message_class`` to the registry.

        Args:
            message_class: A subclass of
                :class:`.flexitkt.flexitkt_messages.backends.base.AbstractMessageSender`.

        Raises:
            ValueError: When a message class with the same :class:`.flexitkt.flexitkt_messages.models.BaseMessage`
                class string already exists in the registry.
        """
        if message_class.get_message_class_string() in self:
            raise ValueError('{} already added to {}'.format(
                message_class.get_message_class_string(), self.get_pretty_classpath()))
        self._message_classes[message_class.get_message_class_string()] = message_class

    def remove(self, message_class_string):
        """
        Remove the message class with the provided ``message_class_string`` from the registry.

        Args:
            message_class_string (str): A unique string identifier of a
            :class:`.flexitkt.flexitkt_messages.BaseMessage` subclass.
        """
        if message_class_string not in self:
            raise ValueError('{} not in {}'.format(message_class_string, self.get_pretty_classpath()))
        del self._message_classes[message_class_string]


class MockableRegistry(Registry):
    """
    A non-singleton version of :class:`.Registry`. For tests.
    """
    def __init__(self):
        self._instance = None
        super().__init__()

    @classmethod
    def make_mockregistry(cls, *message_classes):
        """
        Shortcut for making a mock registry.

        Typical usage in a test::

            from django import test
            from unittest import mock
            from flexitkt.flexitkt_messages import messageclass_registry

            class TestSomething(test.TestCase):
                def test_something(self):
                    mockregistry = messageclass_registry.MockableRegistry.make_mockregistry(
                        <Some model that subclasses BaseMessage>, ...)

                    with mock.patch('flexitkt.flexitkt_messages.messageclass_registry.Registry.get_instance',
                                    lambda: mockregistry):
                        pass  # Your test code here

        Args:
            *message_sender_classes: Zero or more
                :class:`flexitkt.flexitkt_messages.backends.base.AbstractMessageSender`
                subclasses.
        Returns:
            An object of this class with the requested message_sender_classes registered.
        """
        mockregistry = cls()
        for message_class in message_classes:
            mockregistry.add(message_class=message_class)
        return mockregistry
