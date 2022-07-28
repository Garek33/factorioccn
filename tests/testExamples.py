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

    def test_multiline_mod(self):
        circuit = parse('''
            #also test that a comment parses correctly
            in -> x = x + 5 -> int
            int -> x = x % 10 -> out
        ''')
        inp = circuit.wires['in'].signals
        out = circuit.wires['out'].signals
        for i in range(20):
            with self.subTest(i=i):
                inp += SignalSet({ 'x' : i})
                circuit.tick(2)
                self.assertEqual(out['x'], (i+5)%10)

class TestBarrier(unittest.TestCase):
    def setUp(self):
        self.circuit = parse('in -> x > 0 : x -> out')
        self.out = self.circuit.wires['out'].signals

    def test_positive(self):
        self.circuit.wires['in'].signals += SignalSet({'x' : 3})
        self.circuit.tick()
        self.assertEqual(self.out['x'], 3)

    def test_null(self):
        self.circuit.tick()
        self.assertEqual(self.out['x'], 0)
    
    def test_negative(self):
        self.circuit.wires['in'].signals += SignalSet({'x' : -3})
        self.circuit.tick()
        self.assertEqual(self.out['x'], 0)


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