import unittest

from factorioccn.model.combinators import Combinator, BinaryCombinator
from factorioccn.model.core import Frame, Wire


class TestSignalSet(unittest.TestCase):

    def setUp(self):
        self.empty_signals = Frame()
        self.signal_a = Frame({'a': 1})

    def test_default_signals(self):
        self.assertEqual(self.empty_signals, {})
        empty_signals2 = Frame()
        self.assertNotEqual(id(self.empty_signals), id(empty_signals2))

    def test_iadd_basic(self):
        self.empty_signals += self.signal_a
        self.assertEqual(self.empty_signals, self.signal_a)
        self.assertNotEqual(id(self.empty_signals), id(self.signal_a))
        self.assertEqual(self.empty_signals['a'], 1)

    def test_iadd_addition(self):
        self.signal_a += Frame({'a': 2, 'b': 4})
        self.assertEqual(self.signal_a['a'], 3)
        self.assertEqual(self.signal_a['b'], 4)


class TestWire(unittest.TestCase):

    def test_tick(self):
        class Mockcombinator:
            def __init__(self) -> None:
                self.input = Frame()

        wire = Wire()
        wire.outputs.append(Mockcombinator())
        wire.signals += Frame({'a': 1})
        wire.tick()
        self.assertEqual(wire.signals, {})
        self.assertEqual(wire.outputs[0].input, {'a': 1})


class TestCombinator(unittest.TestCase):
    def __init__(self, methodname: str = ...) -> None:
        super().__init__(methodname)

        class MockCombinator(Combinator):
            def __init__(self, output_wires):
                super().__init__(output_wires)
                self.called = False

            def process(self, input):
                self.called = True
                return input

        class Mockwire:
            def __init__(self) -> None:
                self.signals = Frame()

        # noinspection PyTypeChecker
        self.combinator = MockCombinator([Mockwire()])

    def test_tick(self):
        self.combinator.input += Frame({'a': 1})
        self.combinator.tick()
        self.assertTrue(self.combinator.called)
        self.assertEqual(self.combinator.input, {})
        self.assertEqual(self.combinator.output_wires[0].signals, {'a': 1})


class TestBinaryCombinator(unittest.TestCase):
    def __init__(self, methodname: str = ...) -> None:
        super().__init__(methodname)

        # noinspection PyAbstractClass
        class MockCombinator(BinaryCombinator):
            def __init__(self, input_wires, left, right, output_wires):
                super().__init__(input_wires, left, right, output_wires)

        self.combinator = MockCombinator([], 'a', 'b', [])
        self.mock = MockCombinator

    def test_process_arg(self):
        signal_a = Frame({'a': 1})
        empty_signals = Frame()
        self.assertEqual(BinaryCombinator.process_arg(signal_a, 'a'), 1)
        self.assertEqual(BinaryCombinator.process_arg(signal_a, 'b'), 0)
        self.assertEqual(BinaryCombinator.process_arg(empty_signals, 'a'), 0)
        self.assertEqual(BinaryCombinator.process_arg(empty_signals, 'b'), 0)

    def test_select_inputs(self):
        self.assertEqual(self.combinator.select_inputs(Frame({'a': 1, 'c': 2})), ({'a': 1}, 0))
        self.assertEqual(self.combinator.select_inputs(Frame({'a': 1, 'b': 2})), ({'a': 1}, 2))
        self.assertEqual(self.combinator.select_inputs(Frame()), ({'a': 0}, 0))
        self.assertEqual(self.mock([], 'a', '5', []).select_inputs(Frame()), ({'a': 0}, 5))
        self.assertEqual(self.mock([], 'each', '5', []).select_inputs(Frame({'a': 1, 'b': 2})), ({'a': 1, 'b': 2}, 5))
        # TODO: currently missing validation: self.assertRaises(ValueError, lambda: self.combinator.select_inputs(
        #  model.SignalSet(), '5', 'b'))
