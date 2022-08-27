import unittest
from factorioccn.model.combinators import Frame
from factorioccn.model.testing import Test, Tick

from factorioccn.parser import parse

class testTestParsing(unittest.TestCase):
    def setUp(self) -> None:
        self.circuit = parse('''
        foo -> each = each * 0 -> bar

        test testcase {
            0: foo += {a:1, b:2}, bar =~ {a:0}
            1: for 5 bar += {a:1}
            3: bar += {b:2}
            4: bar += {a:2}
            6: bar += {c:3}, foo += {a:2}
            8: foo += {c:3}
        }
        ''')

    def testBasic(self):
        test : Test = self.circuit.tests[0]
        self.assertEqual(test._name, 'testcase')
        self.assertEqual(len(test._ticks), 8)

    def testSetAndExpect(self):
        tick : Tick = self.circuit.tests[0]._ticks[0]
        self.assertEqual(tick._sets[0].wire, 'foo')
        self.assertEqual(tick._sets[0].values, Frame({'a':1, 'b':2}))
        self.assertEqual(tick._expected[0].wire, 'bar')
        self.assertEqual(tick._expected[0].values, Frame({'a':0}))

    def testHold(self):
        test : Test = self.circuit.tests[0]
        for i in range(1,4):
            with self.subTest(i=i):
                val = Frame({'a':1})
                if i == 3:
                    val['b'] = 2
                if i == 4:
                    val['a'] += 2
                sets = test._ticks[i]._sets[0]
                self.assertEqual(sets.wire, 'bar')
                self.assertEqual(sets.values, val)

    def testMultipleSets(self):
        tick : Tick = self.circuit.tests[0]._ticks[6]
        self.assertEqual(tick._sets[0].wire, 'bar')
        self.assertEqual(tick._sets[0].values, Frame({'c':3}))
        self.assertEqual(tick._sets[1].wire, 'foo')
        self.assertEqual(tick._sets[1].values, Frame({'a':2}))
    
    def testSequence(self):
        test : Test = self.circuit.tests[0]
        for i in range(8):
            with self.subTest(i=i):
                t = i
                if i == 7:
                    t = 8
                tick = test._ticks[i]
                self.assertEqual(tick.tick, t)
