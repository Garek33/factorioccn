from collections.abc import MutableMapping, Callable, Sequence, MutableSequence

from factorioccn.model.combinators import BinaryCombinator, Combinator
from model.toplevel import Circuit, Test
from model.core import Frame, Wire
from factorioccn.model.testing import TestExpects, TestOperation, TestSets, Tick


class CircuitBuilder:
    def __init__(self):
        self.wires: MutableMapping[str, Wire] = {}
        self.combinators: MutableSequence[Combinator] = []
        self.tests: MutableSequence[Callable] = []

    def process_wires(self, wires: Sequence[str]):
        for wire in wires:
            if wire not in self.wires:
                self.wires[wire] = Wire()
        return [self.wires[w] for w in wires]

    def register_combinator(self, combinator):
        self.combinators.append(combinator)
        if isinstance(combinator, BinaryCombinator):
            for wire in combinator.input_wires:
                wire.outputs.append(combinator)
        for wire in combinator.output_wires:
            wire.inputs.append(combinator)

    def add_test(self, name: str, ticks: Sequence[Tick]):
        self.tests.append(lambda circuit: Test(name, circuit, ticks))

    def finalize(self):
        circuit = Circuit(self.wires, self.combinators)
        circuit.tests = [t(circuit) for t in self.tests]
        return circuit


class TestTickBuilder:
    def __init__(self, tick: int) -> None:
        self.expects: MutableMapping[str, TestExpects] = {}
        self.sets: MutableMapping[str, TestSets] = {}
        self.tick = tick
        self.holds: 'list[TestHoldBuilder]' = []

    def add_sets(self, op: TestSets):
        self._merge_slice(self.sets, op)

    def add_expects(self, op: TestExpects):
        self._merge_slice(self.expects, op)

    def empty(self):
        return len(self.sets) == 0 and len(self.expects) == 0

    def finalize(self):
        return Tick(self.tick, list(self.expects.values()), list(self.sets.values()))

    @staticmethod
    def _merge_slice(dest: MutableMapping[str, TestOperation], op: TestOperation):
        wire = op.wire
        if wire in dest:
            dest[wire].values += op.values
        else:
            dest[wire] = op.copy()


class TestSetsBuilder:
    def __init__(self, wire: str, signals: Frame):
        self.op = TestSets(wire, signals)

    def __call__(self, tbuilder: TestTickBuilder):
        tbuilder.add_sets(self.op)


class TestExpectsBuilder:
    def __init__(self, wire: str, signals: Frame):
        self.op = TestExpects(wire, signals)

    def __call__(self, tbuilder: TestTickBuilder):
        tbuilder.add_expects(self.op)


class TestHoldBuilder:
    def __init__(self, count: int, children: Sequence[Callable]) -> None:
        self.count = count
        self.children = children

    def __call__(self, tbuilder: TestTickBuilder):
        for c in self.children:
            c(tbuilder)
        self.count -= 1
        return self if self.count > 0 else None
