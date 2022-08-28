from typing import Mapping
import unittest
from factorioccn.model.combinators import Frame, Wire

from factorioccn.model.testing import Signalresult, Test, TestExpects, TestSets, Tick, UnexpectedSignalError

def makeWire(content : Mapping[str, int]):
    w = Wire()
    w.signals = Frame(content)
    return w

class testSignalresult(unittest.TestCase):
    def testSuccess(self):
        res = Signalresult("wire", "stype", 2, 2)
        self.assertTrue(res.isSuccess())

    def testFail(self):
        res = Signalresult("wire", "stype", 2, 3)
        self.assertFalse(res.isSuccess())


class testTestExpects(unittest.TestCase):
    def setUp(self) -> None:
        self.te = TestExpects("wire", Frame({'a' : 1, 'b' : 0}))

    def testSimpleSuccess(self):
        wires = {"wire" : makeWire({'a' : 1, 'b' : 0})}
        results = self.te.test(wires)
        self.assertTrue(results[0].isSuccess())
        self.assertTrue(results[1].isSuccess())

    def testImplicitZero(self):
        wires = {"wire" : makeWire({'a' : 1})}
        results = self.te.test(wires)
        self.assertTrue(results[0].isSuccess())
        self.assertTrue(results[1].isSuccess())

    def testSurplusSignal(self):
        wires = {"wire" : makeWire({'a' : 1, 'b' : 0, 'c' : 4})}
        results = self.te.test(wires)
        self.assertTrue(results[0].isSuccess())
        self.assertTrue(results[1].isSuccess())

    def testMissingValue(self):
        wires = {"wire" : makeWire({'b' : 0})}
        results = self.te.test(wires)
        self.assertFalse(results[0].isSuccess())
        self.assertTrue(results[1].isSuccess())

    def testWrongValue(self):
        wires = {"wire" : makeWire({'a' : 1, 'b' : 4})}
        results = self.te.test(wires)
        self.assertTrue(results[0].isSuccess())
        self.assertFalse(results[1].isSuccess())


class testTestSets(unittest.TestCase):
    def setUp(self) -> None:
        self.wires = {'foo' : Wire(), 'bar' : Wire()}

    def testSetsFresh(self):
        ts = TestSets('foo', Frame({'a' : 1}))
        ts.set(self.wires)
        self.assertEqual(self.wires['foo'].signals, Frame({'a' : 1}))
        self.assertEqual(len(self.wires['bar'].signals), 0)

    def testSetsAdding(self):
        self.wires['foo'].signals = Frame({'a' : 2, 'b' : 5})
        ts = TestSets('foo', Frame({'a' : 1}))
        ts.set(self.wires)
        self.assertEqual(self.wires['foo'].signals, Frame({'a' : 3, 'b' : 5}))
        self.assertEqual(len(self.wires['bar'].signals), 0)


class testTick(unittest.TestCase):
    def setUp(self):
        self.tick = Tick(0, 
            [TestExpects('foo', Frame({'a' : 1})), TestExpects('bar', Frame({'b' : 0}))],
            [TestSets('foo', Frame({'a' : 1}))])
        self.wires = {'foo' : makeWire({'a' : 1}), 'bar' : makeWire({'b' : 0})}

    def testValueMissing(self):
        self.wires['foo'].signals = Frame()
        with self.assertRaisesRegex(UnexpectedSignalError, "unexpected .* dummy:0:\n\tfoo\[a\]: expected 1, actual 0"):
            self.tick.execute(self.wires, 'dummy')

    def testWrongValue(self):
        self.wires['bar'].signals = Frame({'b' : 3})
        with self.assertRaisesRegex(UnexpectedSignalError, "unexpected .* dummy:0:\n\tbar\[b\]: expected 0, actual 3"):
            self.tick.execute(self.wires, 'dummy')

    def testSets(self):
        self.tick.execute(self.wires, 'dummy')
        self.assertEqual(self.wires['foo'].signals, Frame({'a' : 2}))


# noinspection PyTypeChecker
class testTest(unittest.TestCase):
    def testRun(self):
        class MockCircuit:
            def __init__(self) -> None:
                self.wires = {'foo' : makeWire({'a' : 1}), 'bar' : makeWire({'b' : 0})}
                self.t = 0
                self.last = None
            def tick(self, delta):
                self.t += delta
        mc = MockCircuit()

        class MockTick:
            def __init__(self, prev : int, cur : int, mc : MockCircuit, env : unittest.TestCase) -> None:
                self.prev = prev
                self.tick = cur
                self.mc = mc
                self.env = env
            def execute(self, wires, name):
                with self.env.subTest(i=self.tick):
                    for w in wires.values():
                        self.env.assertEqual(w.signals, Frame())
                    self.env.assertEqual(name, 'testtestname')
                    self.env.assertEqual(self.mc.t, self.tick)
                    if self.mc.last is not None:
                        self.env.assertEqual(self.prev, self.mc.last.tick)
        ticks = [MockTick(0,0,mc,self), MockTick(0,2,mc,self), MockTick(2,3,mc,self)]

        Test('testtestname', mc, ticks).run()