from collections.abc import Callable, Sequence, MutableSequence
from typing import MutableMapping

from tatsu.ast import AST
from tatsu.walkers import NodeWalker

from factorioccn.model.combinators import BinaryCombinator, Combinator, ArithmeticCombinator, DeciderCombinator, \
    ConstantCombinator
from factorioccn.model.core import Frame, Wire
from factorioccn.model.testing import TestExpects, TestOperation, TestSets, Tick
from factorioccn.model.toplevel import Circuit, Test


# noinspection PyMethodMayBeStatic
class CommonBuilder(NodeWalker):
    def walk__constframe(self, node: AST):
        try:
            return Frame({s.type: s.value for s in node.signals})
        except AttributeError:  # empty constframe has no signals
            return Frame()


class TestBuilder(CommonBuilder):
    def __init__(self, parent):
        super().__init__()
        self.parent: CircuitBuilder = parent
        self.last = 0
        self.holds: MutableSequence[TestHoldBuilder] = []
        self.ticks: MutableSequence[Tick] = []

    def walk__test(self, node: AST):
        self.walk(node.lines)
        self.parent.add_test(node.name, self.ticks)

    def walk__teststmt(self, node):
        # TODO: handle out-of-order ticks or raise error
        tick = TestTickBuilder(node.tick)
        tick.walk(node.cmds)
        for i in range(self.last + 1, tick.tick):
            gap = TestTickBuilder(i)
            self.holds = [r for r in (h.apply(gap) for h in self.holds) if r]
            if not gap.empty():
                self.ticks.append(gap.finalize())
        self.holds += tick.holds
        self.holds = [r for r in (h.apply(tick) for h in self.holds) if r]
        self.ticks.append(tick.finalize())
        self.last = tick.tick


class CircuitBuilder(CommonBuilder):
    def __init__(self):
        super().__init__()
        self.wires: MutableMapping[str, Wire] = {}
        self.combinators: MutableSequence[Combinator] = []
        self.tests: MutableSequence[Callable] = []

    def walk__circuit(self, node: AST):
        self.walk(node.lines)
        return self._finalize()

    def walk__combinatorstmt(self, node: AST):
        input = self._process_wires(node.input) if node.input is not None else None
        output = self._process_wires(node.output)
        combinator = self.walk(node.action, inputs=input, outputs=output)
        self._register_combinator(combinator)

    # noinspection PyMethodMayBeStatic
    def walk__arithmetic(self, node: AST, inputs, outputs):
        return ArithmeticCombinator(inputs, node.left, node.op, node.right, node.result, outputs)

    # noinspection PyMethodMayBeStatic
    def walk__decider(self, node: AST, inputs, outputs):
        output_signal = node.result.signal
        output_value = node.result.value
        if output_value is not None:
            output_value = 1
        return DeciderCombinator(inputs, node.left, node.op, node.right, output_signal, output_value, outputs)

    # noinspection PyMethodMayBeStatic
    def walk__constant_combinator(self, node: AST, inputs, outputs):
        # TODO: validate no input
        signals = self.walk(node.signals)
        return ConstantCombinator(signals, outputs)

    def walk__test(self, node):
        builder = TestBuilder(self)
        builder.walk(node)

    def _process_wires(self, wires: Sequence[str]):
        for wire in wires:
            if wire not in self.wires:
                self.wires[wire] = Wire()
        return [self.wires[w] for w in wires]

    def _register_combinator(self, combinator):
        self.combinators.append(combinator)
        if isinstance(combinator, BinaryCombinator):
            for wire in combinator.input_wires:
                wire.outputs.append(combinator)
        for wire in combinator.output_wires:
            wire.inputs.append(combinator)

    def add_test(self, name: str, ticks: Sequence[Tick]):
        self.tests.append(lambda circuit: Test(name, circuit, ticks))

    def _finalize(self):
        circuit = Circuit(self.wires, self.combinators)
        circuit.tests = [t(circuit) for t in self.tests]
        return circuit


class TestCmdsBuilder(CommonBuilder):
    def __init__(self):
        super().__init__()
        self.expects: MutableMapping[str, TestExpects] = {}
        self.sets: MutableMapping[str, TestSets] = {}

    def walk__testcmd(self, node: AST):
        self.walk(node.op, wire=node.wire, signals=self.walk(node.signals))

    def walk__testsets(self, _, wire: str, signals: Frame):
        self.add_sets(TestSets(wire, signals))

    def walk__testexpects(self, _, wire: str, signals: Frame):
        self.add_expects(TestExpects(wire, signals))

    @staticmethod
    def _merge_slice(dest: MutableMapping[str, TestOperation], op: TestOperation):
        wire = op.wire
        if wire in dest:
            dest[wire].values += op.values
        else:
            dest[wire] = op.copy()

    def add_sets(self, op: TestSets):
        self._merge_slice(self.sets, op)

    def add_expects(self, op: TestExpects):
        self._merge_slice(self.expects, op)

    def empty(self):
        return len(self.sets) == 0 and len(self.expects) == 0


class TestTickBuilder(TestCmdsBuilder):
    def __init__(self, tick: int):
        super().__init__()
        self.tick = tick
        self.holds: MutableSequence[TestHoldBuilder] = []

    def walk__testhold(self, node):
        builder = TestHoldBuilder(node.count)
        builder.walk(node.cmds)
        self.holds.append(builder)

    def finalize(self):
        return Tick(self.tick, list(self.expects.values()), list(self.sets.values()))


class TestHoldBuilder(TestCmdsBuilder):
    def __init__(self, count: int):
        super().__init__()
        self.count = count

    def apply(self, tick: TestTickBuilder):
        for sets in self.sets.values():
            tick.add_sets(sets)
        for expects in self.expects.values():
            tick.add_expects(expects)
        self.count -= 1
        if self.count > 0:
            return self
