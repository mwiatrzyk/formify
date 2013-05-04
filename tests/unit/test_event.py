import unittest

from formify import event


class TestAddListener(unittest.TestCase):

    def setUp(self):

        class Sender(object):
            pass

        def listener(a):
            return a*2

        event.add_listener(Sender, 'foo', listener)

        self.Sender = Sender
        self.listener = listener

    def test_has_event_listeners(self):
        self.assertTrue(hasattr(self.Sender, '_event_listeners'))

    def test_has_event(self):
        self.assertTrue('foo' in self.Sender._event_listeners)

    def test_has_matching_listener(self):
        self.assertTrue(self.Sender._event_listeners['foo'][0] is self.listener)


class TestAddListenerWithOnAddListener(unittest.TestCase):

    def setUp(self):

        class Sender(object):
            counter = 0

            @classmethod
            def add_listener(cls, event, listener, default_registrar):
                if not hasattr(cls, '_my_events'):
                    cls._my_events = {}
                cls._my_events.setdefault(event, []).append(listener)
                cls.counter += 1

        def listener(a):
            return a*2

        def listener2(a):
            return a*3

        event.add_listener(Sender, 'foo', listener)
        event.add_listener(Sender, 'bar', listener2)

        self.Sender = Sender
        self.listener = listener
        self.listener2 = listener2

    def test_has_event_listeners(self):
        """When :meth:`add_listener` is defined in sender it overrides
        default way of event registration - no ``_event_listeners`` will be
        created by default, unless :meth:`add_listener` does so.
        """
        self.assertFalse(hasattr(self.Sender, '_event_listeners'))

    def test_has_event(self):
        self.assertTrue('foo' in self.Sender._my_events)

    def test_has_listener(self):
        self.assertTrue(self.Sender._my_events['foo'][0] is self.listener)

    def test_called_2_times(self):
        self.assertTrue(self.Sender.counter == 2)


class TestGetListeners(unittest.TestCase):

    def setUp(self):

        class Sender(object):
            _event_listeners = {
                'foo': [1, 2, 3],  # For testing purposes - normally, callables would be here
            }

        self.Sender = Sender

    def test_result(self):
        # When
        listeners = list(event.get_listeners(self.Sender, 'foo'))
        # Then
        self.assertTrue(listeners == [1, 2, 3])


class TestGetListenersWithOnGetListener(unittest.TestCase):

    def setUp(self):

        class Sender(object):

            @classmethod
            def get_listeners(cls, event, default_getter):
                return [1, 2, 3]

        self.Sender = Sender

    def test_result(self):
        # When
        listeners = list(event.get_listeners(self.Sender, 'foo'))
        # Then
        self.assertTrue(listeners == [1, 2, 3])


class TestAliasOf(unittest.TestCase):

    def test_make_alias(self):
        # Given
        class RealSender(object):
            pass
        class Sender(object):
            pass
        # When
        event.alias_of(Sender, RealSender)
        # Then
        self.assertTrue(hasattr(Sender, '_event_alias_of'))
        self.assertTrue(hasattr(Sender, '_event_alias_flags'))

    def test_register_via_alias(self):
        # Given
        class RealSender(object):
            pass
        class Sender(object):
            pass
        def test():
            pass
        event.alias_of(Sender, RealSender)
        # When
        event.add_listener(Sender, 'test', test)
        # Then
        self.assertTrue(hasattr(RealSender, '_event_listeners'))
        self.assertIn('test', RealSender._event_listeners)
        self.assertIs(RealSender._event_listeners['test'][0], test)

    def test_read_only_alias(self):
        # Given
        class RealSender(object):
            _event_listeners = {
                'foo': [1, 2, 3]
            }
        class Sender(object):
            pass
        def test():
            pass
        event.alias_of(Sender, RealSender, event.F_READ_ACCESS)
        # When
        def setter():
            event.add_listener(Sender, 'test', test)
        result = event.get_listeners(Sender, 'foo')
        # Then
        self.assertRaises(TypeError, setter)
        self.assertEqual(result, [1, 2, 3])


class TestNotify(unittest.TestCase):

    def setUp(self):

        def foo(a):
            self.foo = a
            self.order.append(self.foo)

        def bar(a):
            self.bar = a * 2
            self.order.append(self.bar)

        class Sender(object):
            _event_listeners = {
                'foo': [foo, bar]
            }

        self.order = []
        self.Sender = Sender

    def test_notify(self):
        # When
        event.notify(self.Sender, 'foo', 1)
        # Then
        self.assertTrue(self.foo == 1)
        self.assertTrue(self.bar == 2)

    def test_notify_order(self):
        # When
        event.notify(self.Sender, 'foo', 1)
        # Then
        self.assertTrue(self.order == [1, 2])


class TestPipeline(unittest.TestCase):

    def setUp(self):

        def f1(value):
            return value[:-1]

        def f2(foo=None):
            return foo * 2

        class Sender1(object):
            _event_listeners = {
                'foo': [f1]
            }

        class Sender2(object):
            _event_listeners = {
                'foo': [f2]
            }

        self.Sender1 = Sender1
        self.Sender2 = Sender2

    def test_for_args(self):
        # When
        result = event.pipeline(self.Sender1, 'foo', 0, 'test')
        # Then
        self.assertTrue(result == 'tes')

    def test_for_kwargs(self):
        # When
        result = event.pipeline(self.Sender2, 'foo', 'foo', foo=2)
        # Then
        self.assertTrue(result == 4)


class TestListensFor(unittest.TestCase):

    def setUp(self):

        class Sender(object):
            pass

        self.Sender = Sender

    def test_no_event(self):
        # When
        try:
            event.listens_for(self.Sender)
        except TypeError:
        # Then
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_decorate(self):
        # When

        @event.listens_for(self.Sender, 'foo')
        def listener():
            pass

        # Then
        self.assertTrue(self.Sender._event_listeners['foo'][0] is listener)

    def test_decorate_complex_event(self):
        # When

        @event.listens_for(self.Sender, 'foo', 'bar')
        def listener():
            pass

        # Then
        self.assertTrue(('foo', 'bar') in self.Sender._event_listeners)
