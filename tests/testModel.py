from operator import mod
from statistics import mode
import unittest

from factorioccn import model

class TestSignalSet(unittest.TestCase):

    def setUp(self):
        self.empty_signals = model.Frame()
        self.signal_a = model.Frame({'a' : 1})

    def test_default_signals(self):
        self.assertEqual(self.empty_signals._data, {})
        empty_signals2 = model.Frame()
        self.assertNotEqual(id(self.empty_signals._data), id(empty_signals2._data))

    def test_iadd_basic(self):
        self.empty_signals += self.signal_a
        self.assertEqual(self.empty_signals._data, self.signal_a._data)
        self.assertNotEqual(id(self.empty_signals._data), id(self.signal_a._data))
        self.assertEqual(self.empty_signals._data['a'], 1)

    def test_iadd_addition(self):
        self.signal_a += model.Frame({'a' : 2, 'b' : 4})
        self.assertEqual(self.signal_a._data['a'], 3)
        self.assertEqual(self.signal_a._data['b'], 4)

class TestWire(unittest.TestCase):

    def test_tick(self):
        class Mockcombinator:
            def __init__(self) -> None:
                self.input = model.Frame()
        wire = model.Wire()
        wire.outputs.append(Mockcombinator())
        wire.signals += model.Frame({'a' : 1})
        wire.tick()
        self.assertEqual(wire.signals._data, {})
        self.assertEqual(wire.outputs[0].input._data, {'a' : 1})


class TestCombinator(unittest.TestCase):
    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        class MockCombinator(model.Combinator):
            def __init__(self, output_wires):
                super().__init__(output_wires)
                self.called = False
            def process(self, input):
                self.called = True
                return input
        class Mockwire:
            def __init__(self) -> None:
                self.signals = model.Frame()
        self.combinator = MockCombinator([Mockwire()])

    def test_tick(self):
        self.combinator.input += model.Frame({'a' : 1 })
        self.combinator.tick()
        self.assertTrue(self.combinator.called)
        self.assertEqual(self.combinator.input._data, {})
        self.assertEqual(self.combinator.output_wires[0].signals._data, {'a' : 1})


class TestBinaryCombinator(unittest.TestCase):
    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        class MockCombinator(model.BinaryCombinator):
            def __init__(self, input_wires, left, right, output_wires):
                super().__init__(input_wires, left, right, output_wires)
        self.combinator = MockCombinator([], 'a', 'b', [])
        self.mock = MockCombinator

    def test_process_arg(self):
        signal_a = model.Frame({'a' : 1})
        empty_signals = model.Frame()
        self.assertEqual(model.BinaryCombinator.process_arg(signal_a, 'a'), 1)
        self.assertEqual(model.BinaryCombinator.process_arg(signal_a, 'b'), 0)
        self.assertEqual(model.BinaryCombinator.process_arg(empty_signals, 'a'), 0)
        self.assertEqual(model.BinaryCombinator.process_arg(empty_signals, 'b'), 0)

    def test_select_inputs(self):
        self.assertEqual(self.combinator.select_inputs(model.Frame({'a' : 1, 'c' : 2})), ({'a' : 1}, 0))
        self.assertEqual(self.combinator.select_inputs(model.Frame({'a' : 1, 'b' : 2})), ({'a' : 1}, 2))
        self.assertEqual(self.combinator.select_inputs(model.Frame()), ({'a' : 0}, 0))
        self.assertEqual(self.mock([], 'a', '5', []).select_inputs(model.Frame()), ({'a' : 0}, 5))
        self.assertEqual(self.mock([], 'each', '5', []).select_inputs(model.Frame({'a' : 1, 'b' : 2})), ({'a' : 1, 'b' : 2}, 5))
        #TODO: currently missing validation: self.assertRaises(ValueError, lambda: self.combinator.select_inputs(model.SignalSet(), '5', 'b'))