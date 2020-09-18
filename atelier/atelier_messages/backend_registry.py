from ievv_opensource.utils.singleton import Singleton


class Registry(Singleton):
    """
    Registry of flexitkt_messagees message sender types.

    Holds exactly one subclass of :class:`.flexitkt.flexitkt_messagees.backends.base.AbstractMessageSender` for each
    `message_type`.

    Outside tests you will not instantiate this, but rather use::

        Registry.get_instance()
    """
    def __init__(self):
        super().__init__()
        self._backend_sender_classes = {}

    def __contains__(self, message_type):
        """
        Implement "in"-operator support for ``Registry._sender_classes``.
        """
        return message_type in self._backend_sender_classes

    def __iter__(self):
        """
        Iterate over the registry yielding
        subclasses of :class:`.flexitkt.flexitkt_messagees.backends.base.AbstractMessageSender`.
        """
        return iter(self._backend_sender_classes.values())

    def get_pretty_classpath(self):
        """
        Prettified string of the registry path.
        """
        return '{}.{}'.format(self.__module__, self.__class__.__name__)

    def get(self, message_type):
        """
        Get a subclass of :class:`.flexitkt.flexitkt_messagees.backends.base.AbstractMessageSender` stored in the
        registry by the ``message_type``

        Args:
            message_type (str): A :obj:`.flexitkt.flexitkt_messagees.backends.base.AbstractMessageSender.message_type`.
        """
        if message_type not in self:
            raise ValueError('{} not in {}'.format(message_type, self.get_pretty_classpath()))
        return self._backend_sender_classes[message_type]

    def add(self, message_sender_class):
        """
        Add the provided ``message_sender_class`` to the registry.

        Args:
            message_sender_class: A subclass of
                :class:`.flexitkt.flexitkt_messagees.backends.base.AbstractMessageSender`.

        Raises:
            ValueError: When a message sender class with the same
                :obj:`.flexitkt.flexitkt_messagees.backends.base.AbstractMessageSender.message_type` already exists in
                the registry.
        """
        if message_sender_class.get_message_type() in self:
            raise ValueError('{} already added to {}'.format(
                message_sender_class.get_message_type(), self.get_pretty_classpath()))
        self._backend_sender_classes[message_sender_class.get_message_type()] = message_sender_class

    def remove(self, message_type):
        """
        Remove the message sender class with the provided `message_type` from the registry.

        Args:
            message_type (str): A :obj:`.flexitkt.flexitkt_messagees.backends.base.AbstractMessageSender.message_type`.
        """
        if message_type not in self:
            raise ValueError('{} not in {}'.format(message_type, self.get_pretty_classpath()))
        del self._backend_sender_classes[message_type]


class MockableRegistry(Registry):
    """
    A non-singleton version of :class:`.Registry`. For tests.
    """
    def __init__(self):
        self._instance = None
        super().__init__()

    @classmethod
    def make_mockregistry(cls, *message_sender_classes):
        """
        Shortcut for making a mock registry.

        Typical usage in a test::

            from django import test
            from unittest import mock
            from flexitkt.flexitkt_messagees.backends.base import AbstractMessageSender
            from flexitkt.flexitkt_messagees import backend_registry

            class TestSomething(test.TestCase):
                def test_something(self):
                    class Mock1(AbstractMessageSender):
                        message_type = 'Mock1'

                    class Mock2(AbstractMessageSender):
                        container_type = 'Mock2'

                    mockregistry = backend_registry.MockableRegistry.make_mockregistry(
                        Mock1, Mock2)

                    with mock.patch('flexitkt.flexitkt_messagees.backend_registry.Registry.get_instance',
                                    lambda: mockregistry):
                        pass  # Your test code here

        Args:
            *message_sender_classes: Zero or more
                :class:`flexitkt.flexitkt_messagees.backends.base.AbstractMessageSender`
                subclasses.
        Returns:
            An object of this class with the requested message_sender_classes registered.
        """
        mockregistry = cls()
        for message_sender_class in message_sender_classes:
            mockregistry.add(message_sender_class=message_sender_class)
        return mockregistry
