from operator import mod
from statistics import mode
import unittest

from factorioccn import model

class TestSignalSet(unittest.TestCase):

    def setUp(self):
        self.empty_signals = model.SignalSet()
        self.signal_a = model.SignalSet({'a' : 1})

    def test_default_signals(self):
        self.assertEqual(self.empty_signals._data, {})
        empty_signals2 = model.SignalSet()
        self.assertNotEqual(id(self.empty_signals._data), id(empty_signals2._data))

    def test_iadd_basic(self):
        self.empty_signals += self.signal_a
        self.assertEqual(self.empty_signals._data, self.signal_a._data)
        self.assertNotEqual(id(self.empty_signals._data), id(self.signal_a._data))
        self.assertEqual(self.empty_signals._data['a'], 1)

    def test_iadd_addition(self):
        self.signal_a += model.SignalSet({'a' : 2, 'b' : 4})
        self.assertEqual(self.signal_a._data['a'], 3)
        self.assertEqual(self.signal_a._data['b'], 4)

    def test_determine_arg(self):
        self.assertEqual(self.signal_a.determine_arg('a'), 1)
        self.assertEqual(self.signal_a.determine_arg('b'), 0)
        self.assertEqual(self.empty_signals.determine_arg('a'), 0)
        self.assertEqual(self.empty_signals.determine_arg('b'), 0)


class TestWire(unittest.TestCase):

    def test_tick(self):
        class Mockcombinator:
            def __init__(self) -> None:
                self.input = model.SignalSet()
        wire = model.Wire()
        wire.outputs.append(Mockcombinator())
        wire.signals += model.SignalSet({'a' : 1})
        wire.tick()
        self.assertEqual(wire.signals._data, {})
        self.assertEqual(wire.outputs[0].input._data, {'a' : 1})


class TestCombinator(unittest.TestCase):

    def test_tick(self):
        class Mockwire:
            def __init__(self) -> None:
                self.signals = model.SignalSet()
        class DummyCombinator(model.Combinator):
            called = False
            def process(self, input):
                DummyCombinator.called = True
                return input
        combinator = DummyCombinator([], [Mockwire()])
        combinator.input += model.SignalSet({'a' : 1 })
        combinator.tick()
        self.assertTrue(DummyCombinator.called)
        self.assertEqual(combinator.input._data, {})
        self.assertEqual(combinator.output_wires[0].signals._data, {'a' : 1})