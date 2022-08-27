from distutils.command.build import build
from typing import Mapping, Sequence
from tatsu.walkers import DepthFirstWalker

from factorioccn.model.combinators import Frame, DeciderCombinator, ArithmeticCombinator, ConstantCombinator
from factorioccn.model.testing import Slice
from factorioccn.parser.builders import CircuitBuilder, TestHoldBuilder, TestTickBuilder

class Walker(DepthFirstWalker):

    def walk_Script(self, _, children):
        cbuilder = CircuitBuilder()
        for element in children:
            element(cbuilder)
        return cbuilder.finalize()

    def walk_Test(self, node, children: Sequence[TestTickBuilder]):
        name = node.name
        holds = []
        ticks = []
        last = 0
        for c in children:
            for i in range(last+1, c.tick):
                builder = TestTickBuilder(i)
                holds = [r for r in [h(builder) for h in holds] if r]
                if not builder.empty():
                    ticks.append(builder.finalize())
            holds += c.holds
            holds = [r for r in [h(c) for h in holds] if r]
            ticks.append(c.finalize())
            last = c.tick
        return lambda cbuilder: cbuilder.addTest(name, ticks)

    def walk_Teststmt(self, node, children):
        builder = TestTickBuilder(node.tick)
        for c in children:
            c(builder)
        return builder

    def walk_Testcmd(self, node, children):
        slice = Slice(node.wire, children[0])
        if node.op == '=~':
            return lambda builder: builder.addExpecteds(slice)
        else:
            return lambda builder: builder.addSets(slice)

    def walk_Testhold(self, node, children):
        return lambda builder: builder.holds.append(TestHoldBuilder(node.count, children))

    def walk_Combinatorstmt(self, node, children):
        parts = {x[0]:x[1] for x in children}
        input = parts[node.input] if node.input is not None else lambda _: []
        output = parts[node.output]
        combinator = parts[node.action]
        def createCombinator(cbuilder):
            actual = combinator(input(cbuilder), output(cbuilder))
            cbuilder.registerCombinator(actual)
        return createCombinator

    def walk_Wires(self, node, _):
        return (node, lambda cbuilder: cbuilder.processWires(node.wires))

    def walk_Decider(self, node, _):
        output_signal = node.result.signal
        output_value = node.result.value
        if output_value is not None:
            output_value = 1
        return (node, lambda inputs, outputs: DeciderCombinator(inputs, node.left, node.op, node.right, output_signal, output_value, outputs))
        
    def walk_Arithmetic(self, node, _):
        return (node, lambda inputs, outputs: ArithmeticCombinator(inputs, node.left, node.op, node.right, node.result, outputs))

    def walk_ConstantCombinator(self, node, children):
        #TODO: validate no input
        return (node, lambda _, outputs: ConstantCombinator(children[0], outputs))

    def walk_Constframe(self, node, _):
        return Frame({s.type : s.value for s in node.signals})
