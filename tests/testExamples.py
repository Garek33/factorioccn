import unittest

from factorioccn.parser import parse
from factorioccn.model import Circuit, SignalSet

class TestBasic(unittest.TestCase):
    def test_plus(self):
        circuit = parse('in -> x = x + 1 -> out')
        circuit.wires['in'].signals += SignalSet({'x' : 1})
        circuit.tick()
        self.assertEqual(circuit.wires['out'].signals['x'], 2)

    def test_clock(self):
        circuit = parse('clk -> x = x + 1 -> clk')
        self.assertEqual(circuit.wires['clk'].signals._data, {})
        circuit.tick()
        self.assertEqual(circuit.wires['clk'].signals['x'], 1)
        circuit.tick(5)
        self.assertEqual(circuit.wires['clk'].signals['x'], 6)


class TestLatch(unittest.TestCase):
    def setUp(self):
        self.circuit = parse('data -> S > R : S(1) -> data')
        self.data = self.circuit.wires['data']
        self.data.signals += SignalSet({ 'S' : 1})

    def test_set(self):
        self.circuit.tick()
        self.assertEqual(self.data.signals['S'], 1)
        self.circuit.tick(5)
        self.assertEqual(self.data.signals['S'], 1)

    def test_reset(self):
        self.data.signals += SignalSet({ 'R' : 1})
        self.circuit.tick()
        self.assertEqual(self.data.signals['S'], 0)
        self.assertEqual(self.data.signals['R'], 0)