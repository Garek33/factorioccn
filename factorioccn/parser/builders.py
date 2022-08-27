from typing import Callable, Mapping, Sequence
from factorioccn.model.combinators import BinaryCombinator, Circuit, Frame, Wire
from factorioccn.model.testing import Slice, Test, Tick


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

    def addTest(self, name : str, ticks : Sequence[Tick]):
        self.tests.append(Test(name, self.circuit, ticks))

    def finalize(self):
        for test in self.tests:
            test.run()
        return self.circuit

    
class TestTickBuilder:
    def __init__(self, tick: int) -> None:
        self.expecteds: Mapping[str,Slice] = {}
        self.sets: Mapping[str,Slice] = {}
        self.tick = tick
        self.holds: 'list[TestHoldBuilder]' = []

    def addSets(self, slice: Slice):
        self._mergeSlice(self.sets, slice)
    
    def addExpecteds(self, slice: Slice):
        self._mergeSlice(self.expecteds, slice)

    def empty(self):
        return len(self.sets) == 0 and len(self.expecteds) == 0

    def finalize(self):
        return Tick(self.tick, self.expecteds.values(), self.sets.values())

    def _mergeSlice(self, map: Mapping[str,Slice], slice: Slice):
        wire = slice.wire
        if wire in map:
            map[wire].values += slice.values
        else:
            map[wire] = slice.copy()


class TestHoldBuilder:
    def __init__(self, count: int, children: Sequence[Callable]) -> None:
        self.count = count
        self.children = children

    def __call__(self, tbuilder: TestTickBuilder):
        for c in self.children:
            c(tbuilder)
        self.count -= 1
        return self if self.count > 0 else None