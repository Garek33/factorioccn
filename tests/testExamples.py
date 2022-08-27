import unittest

from factorioccn.parser import parse
from factorioccn.model.combinators import Frame

class TestBasic(unittest.TestCase):
    def test_plus(self):
        circuit = parse('in -> x = x + 1 -> out')
        circuit.wires['in'].signals += Frame({'x' : 1})
        circuit.tick()
        self.assertEqual(circuit.wires['out'].signals['x'], 2)

    def test_clock(self):
        circuit = parse('clk -> x = x + 1 -> clk')
        self.assertEqual(circuit.wires['clk'].signals, {})
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
                inp += Frame({ 'x' : i})
                circuit.tick(2)
                self.assertEqual(out['x'], (i+5)%10)


class TestWildcardArithmetic(unittest.TestCase):
    def test_sum(self):
        circuit = parse('in -> x = each * 1 -> out')
        circuit.wires['in'].signals += Frame({'a' : 1, 'b' : 2, 'c' : 3})
        circuit.tick()
        self.assertEqual(circuit.wires['out'].signals['x'], 6)
        self.assertEqual(circuit.wires['out'].signals['a'], 0)
        self.assertEqual(circuit.wires['out'].signals['b'], 0)
        self.assertEqual(circuit.wires['out'].signals['c'], 0)
    
    def test_double(self):
        circuit = parse('in -> each = each * 2 -> out')
        circuit.wires['in'].signals += Frame({'a' : 1, 'b' : 2, 'c' : 3})
        circuit.tick()
        self.assertEqual(circuit.wires['out'].signals['x'], 0)
        self.assertEqual(circuit.wires['out'].signals['a'], 2)
        self.assertEqual(circuit.wires['out'].signals['b'], 4)
        self.assertEqual(circuit.wires['out'].signals['c'], 6)


class TestWildcardDecider(unittest.TestCase):
    def setUp(self):
        self.signals = Frame({'a' : 1, 'b' : 2, 'c' : 3})

    def _run(self, circuit):
        circuit.wires['in'].signals += self.signals
        circuit.tick()
    
    def test_signal_signal_value(self):
        circuit = parse('in -> b > 1 : c -> out')
        self._run(circuit)
        self.assertEqual(circuit.wires['out'].signals['a'], 0)
        self.assertEqual(circuit.wires['out'].signals['b'], 0)
        self.assertEqual(circuit.wires['out'].signals['c'], 3)
    
    def test_each_each_single(self):
        circuit = parse('in -> each > 1 : each(1) -> out')
        self._run(circuit)
        self.assertEqual(circuit.wires['out'].signals['a'], 0)
        self.assertEqual(circuit.wires['out'].signals['b'], 1)
        self.assertEqual(circuit.wires['out'].signals['c'], 1)
    
    def test_each_each_value(self):
        circuit = parse('in -> each > 1 : each -> out')
        self._run(circuit)
        self.assertEqual(circuit.wires['out'].signals['a'], 0)
        self.assertEqual(circuit.wires['out'].signals['b'], 2)
        self.assertEqual(circuit.wires['out'].signals['c'], 3)
    
    def test_each_signal_single(self):
        circuit = parse('in -> each > 1 : x(1) -> out')
        self._run(circuit)
        self.assertEqual(circuit.wires['out'].signals['a'], 0)
        self.assertEqual(circuit.wires['out'].signals['b'], 0)
        self.assertEqual(circuit.wires['out'].signals['c'], 0)
        self.assertEqual(circuit.wires['out'].signals['x'], 3)
        
    def test_each_signal_value(self):
        circuit = parse('in -> each > 1 : x -> out')
        self._run(circuit)
        self.assertEqual(circuit.wires['out'].signals['a'], 0)
        self.assertEqual(circuit.wires['out'].signals['b'], 0)
        self.assertEqual(circuit.wires['out'].signals['c'], 0)
        self.assertEqual(circuit.wires['out'].signals['x'], 5)
    
    def test_all_false(self):
        circuit = parse('in -> everything > 1 : everything(1) -> out')
        self._run(circuit)
        self.assertEqual(circuit.wires['out'].signals['a'], 0)
        self.assertEqual(circuit.wires['out'].signals['b'], 0)
        self.assertEqual(circuit.wires['out'].signals['c'], 0)
    
    def test_all_all_single(self):
        circuit = parse('in -> everything > -1 : everything(1) -> out')
        self._run(circuit)
        self.assertEqual(circuit.wires['out'].signals['a'], 1)
        self.assertEqual(circuit.wires['out'].signals['b'], 1)
        self.assertEqual(circuit.wires['out'].signals['c'], 1)

    def test_all_all_value(self):
        circuit = parse('in -> everything > -1 : everything -> out')
        self._run(circuit)
        self.assertEqual(circuit.wires['out'].signals['a'], 1)
        self.assertEqual(circuit.wires['out'].signals['b'], 2)
        self.assertEqual(circuit.wires['out'].signals['c'], 3)

    def test_any_all_single(self):
        circuit = parse('in -> anything > 1 : everything(1) -> out')
        self._run(circuit)
        self.assertEqual(circuit.wires['out'].signals['a'], 1)
        self.assertEqual(circuit.wires['out'].signals['b'], 1)
        self.assertEqual(circuit.wires['out'].signals['c'], 1)

    def test_any_all_value(self):
        circuit = parse('in -> anything > 1 : everything -> out')
        self._run(circuit)
        self.assertEqual(circuit.wires['out'].signals['a'], 1)
        self.assertEqual(circuit.wires['out'].signals['b'], 2)
        self.assertEqual(circuit.wires['out'].signals['c'], 3)
        
    def test_any_any_value(self):
        circuit = parse('in -> anything > 1 : anything -> out')
        self._run(circuit)
        self.assertEqual(circuit.wires['out'].signals['a'], 0)
        self.assertEqual(circuit.wires['out'].signals['b'], 2)
        self.assertEqual(circuit.wires['out'].signals['c'], 0)



class TestBarrier(unittest.TestCase):
    def setUp(self):
        self.circuit = parse('in -> x > 0 : x -> out')
        self.out = self.circuit.wires['out'].signals

    def test_positive(self):
        self.circuit.wires['in'].signals += Frame({'x' : 3})
        self.circuit.tick()
        self.assertEqual(self.out['x'], 3)

    def test_null(self):
        self.circuit.tick()
        self.assertEqual(self.out['x'], 0)
    
    def test_negative(self):
        self.circuit.wires['in'].signals += Frame({'x' : -3})
        self.circuit.tick()
        self.assertEqual(self.out['x'], 0)


class TestLatch(unittest.TestCase):
    def setUp(self):
        self.circuit = parse('data -> S > R : S(1) -> data')
        self.data = self.circuit.wires['data']
        self.data.signals += Frame({ 'S' : 1})

    def test_set(self):
        self.circuit.tick()
        self.assertEqual(self.data.signals['S'], 1)
        self.circuit.tick(5)
        self.assertEqual(self.data.signals['S'], 1)

    def test_reset(self):
        self.data.signals += Frame({ 'R' : 1})
        self.circuit.tick()
        self.assertEqual(self.data.signals['S'], 0)
        self.assertEqual(self.data.signals['R'], 0)


class TestConstant(unittest.TestCase):
    def test_empty(self):
        circuit = parse('{} -> data')
        circuit.tick()
        self.assertEqual(len(circuit.wires['data'].signals), 0)
    
    def test_single(self):
        circuit = parse('{signal-a(4)} -> data')
        circuit.tick()
        self.assertEqual(circuit.wires['data'].signals, {'signal-a': 4})
    
    def test_empty(self):
        circuit = parse('{signal-a(4), signal-b(5)} -> data')
        circuit.tick()
        self.assertEqual(circuit.wires['data'].signals, {'signal-a': 4, 'signal-b': 5})