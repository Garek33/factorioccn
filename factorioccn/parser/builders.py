from collections.abc import MutableMapping
from typing import Callable, Sequence

from factorioccn.model.combinators import BinaryCombinator, Circuit, Frame, Wire
from factorioccn.model.testing import TestExpects, TestOperation, Test, TestSets, Tick


class CircuitBuilder:
    def __init__(self):
        self.circuit = Circuit()
        self.tests: list[Test] = []

    def processWires(self, wireset):
        for wire in wireset:
            if wire not in self.circuit.wires:
                self.circuit.wires[wire] = Wire()
        return [self.circuit.wires[w] for w in wireset]

    def registerCombinator(self, combinator):
        self.circuit.combinators.append(combinator)
        if isinstance(combinator, BinaryCombinator):
            for wire in combinator.input_wires:
                wire.outputs.append(combinator)
        for wire in combinator.output_wires:
            wire.inputs.append(combinator)

    def addTest(self, name: str, ticks: Sequence[Tick]):
        self.tests.append(Test(name, self.circuit, ticks))

    def finalize(self):
        for test in self.tests:
            test.run()
        self.circuit.tests = self.tests
        return self.circuit


class TestTickBuilder:
    def __init__(self, tick: int) -> None:
        self.expecteds: MutableMapping[str, TestExpects] = {}
        self.sets: MutableMapping[str, TestSets] = {}
        self.tick = tick
        self.holds: 'list[TestHoldBuilder]' = []

    def addSets(self, slice: TestSets):
        self._mergeSlice(self.sets, slice)

    def addExpects(self, slice: TestExpects):
        self._mergeSlice(self.expecteds, slice)

    def empty(self):
        return len(self.sets) == 0 and len(self.expecteds) == 0

    def finalize(self):
        return Tick(self.tick, list(self.expecteds.values()), list(self.sets.values()))

    def _mergeSlice(self, map: MutableMapping[str, TestOperation], slice: TestOperation):
        wire = slice.wire
        if wire in map:
            map[wire].values += slice.values
        else:
            map[wire] = slice.copy()


class TestSetsBuilder:
    def __init__(self, wire: str, signals: Frame):
        self.op = TestSets(wire, signals)

    def __call__(self, tbuilder: TestTickBuilder):
        tbuilder.addSets(self.op)


class TestExpectsBuilder:
    def __init__(self, wire: str, signals: Frame):
        self.op = TestExpects(wire, signals)

    def __call__(self, tbuilder: TestTickBuilder):
        tbuilder.addExpects(self.op)


class TestHoldBuilder:
    def __init__(self, count: int, children: Sequence[Callable]) -> None:
        self.count = count
        self.children = children

    def __call__(self, tbuilder: TestTickBuilder):
        for c in self.children:
            c(tbuilder)
        self.count -= 1
        return self if self.count > 0 else None
