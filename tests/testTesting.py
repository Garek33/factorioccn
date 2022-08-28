import unittest
from typing import Mapping

from model.core import Frame, Wire
from factorioccn.model.testing import SignalTest, TestExpects, TestSets, Tick, WrongSignalError
from model.toplevel import Test


def make_wire(content: Mapping[str, int]):
    w = Wire()
    w.signals = Frame(content)
    return w


class TestSignalTest(unittest.TestCase):
    def testSuccess(self):
        res = SignalTest("wire", "stype", 2, 2)
        self.assertTrue(res.is_success())

    def testFail(self):
        res = SignalTest("wire", "stype", 2, 3)
        self.assertFalse(res.is_success())


class TestTestExpects(unittest.TestCase):
    def setUp(self) -> None:
        self.te = TestExpects("wire", Frame({'a': 1, 'b': 0}))

    def testSimpleSuccess(self):
        wires = {"wire": make_wire({'a': 1, 'b': 0})}
        results = self.te.test(wires)
        self.assertTrue(results[0].is_success())
        self.assertTrue(results[1].is_success())

    def testImplicitZero(self):
        wires = {"wire": make_wire({'a': 1})}
        results = self.te.test(wires)
        self.assertTrue(results[0].is_success())
        self.assertTrue(results[1].is_success())

    def testSurplusSignal(self):
        wires = {"wire": make_wire({'a': 1, 'b': 0, 'c': 4})}
        results = self.te.test(wires)
        self.assertTrue(results[0].is_success())
        self.assertTrue(results[1].is_success())

    def testMissingValue(self):
        wires = {"wire": make_wire({'b': 0})}
        results = self.te.test(wires)
        self.assertFalse(results[0].is_success())
        self.assertTrue(results[1].is_success())

    def testWrongValue(self):
        wires = {"wire": make_wire({'a': 1, 'b': 4})}
        results = self.te.test(wires)
        self.assertTrue(results[0].is_success())
        self.assertFalse(results[1].is_success())


class TestTestSets(unittest.TestCase):
    def setUp(self) -> None:
        self.wires = {'foo': Wire(), 'bar': Wire()}

    def testSetsFresh(self):
        ts = TestSets('foo', Frame({'a': 1}))
        ts.set(self.wires)
        self.assertEqual(self.wires['foo'].signals, Frame({'a': 1}))
        self.assertEqual(len(self.wires['bar'].signals), 0)

    def testSetsAdding(self):
        self.wires['foo'].signals = Frame({'a': 2, 'b': 5})
        ts = TestSets('foo', Frame({'a': 1}))
        ts.set(self.wires)
        self.assertEqual(self.wires['foo'].signals, Frame({'a': 3, 'b': 5}))
        self.assertEqual(len(self.wires['bar'].signals), 0)


# noinspection PyPep8
class TestTick(unittest.TestCase):
    def setUp(self):
        self.tick = Tick(0,
                         [TestExpects('foo', Frame({'a': 1})), TestExpects('bar', Frame({'b': 0}))],
                         [TestSets('foo', Frame({'a': 1}))])
        self.wires = {'foo': make_wire({'a': 1}), 'bar': make_wire({'b': 0})}

    def testValueMissing(self):
        self.wires['foo'].signals = Frame()
        with self.assertRaisesRegex(WrongSignalError, "unexpected .* dummy:0:\n\tfoo\[a\]: expected 1, actual 0"):
            self.tick.execute(self.wires, 'dummy')

    def testWrongValue(self):
        self.wires['bar'].signals = Frame({'b': 3})
        with self.assertRaisesRegex(WrongSignalError, "unexpected .* dummy:0:\n\tbar\[b\]: expected 0, actual 3"):
            self.tick.execute(self.wires, 'dummy')

    def testSets(self):
        self.tick.execute(self.wires, 'dummy')
        self.assertEqual(self.wires['foo'].signals, Frame({'a': 2}))


# noinspection PyTypeChecker
class TestTest(unittest.TestCase):
    def testRun(self):
        class MockCircuit:
            def __init__(self) -> None:
                self.wires = {'foo': make_wire({'a': 1}), 'bar': make_wire({'b': 0})}
                self.t = 0
                self.last = None

            def tick(self, delta):
                self.t += delta

        mc = MockCircuit()
        outer = self

        class MockTick:
            def __init__(self, prev: int, cur: int) -> None:
                self.prev = prev
                self.tick = cur

            def execute(self, wires, name):
                with outer.subTest(i=self.tick):
                    for w in wires.values():
                        outer.assertEqual(w.signals, Frame())
                    outer.assertEqual(name, 'testtestname')
                    outer.assertEqual(mc.t, self.tick)
                    if mc.last is not None:
                        outer.assertEqual(self.prev, mc.last.tick)

        ticks = [MockTick(0, 0), MockTick(0, 2), MockTick(2, 3)]

        Test('testtestname', mc, ticks).run()
