from typing import Mapping
from tatsu.walkers import DepthFirstWalker

from factorioccn.model.combinators import Frame, DeciderCombinator, ArithmeticCombinator, ConstantCombinator
from factorioccn.model.testing import Slice, Tick
from factorioccn.parser.builders import CircuitBuilder, TestTickBuilder

class Walker(DepthFirstWalker):

    def walk_Script(self, _, children):
        cbuilder = CircuitBuilder()
        for element in children:
            element(cbuilder)
        return cbuilder.finalize()

    def walk_Test(self, node, children):
        name = node.name
        ticks = [c for c in children if not isinstance(c,str)]
        return lambda cbuilder: cbuilder.addTest(name, ticks)

    def walk_Teststmt(self, node, children):
        builder = TestTickBuilder()
        for c in children:
            c(builder)
        return builder.finalize(node.tick)

    def walk_Testcmd(self, node, children):
        if node.op == 'expect':
            add = TestTickBuilder.addExpecteds
        else:
            add = TestTickBuilder.addSets
        def process(builder: TestTickBuilder):
            for slice in children:
                add(builder, slice)
        return process
    
    def walk_Testkv(self, node, children):
        if node.value is None:
            frame = children[0]
        else:
            if len(node.slice) != 1: #pragma: no cover
                pass #TODO: raise error
            frame = Frame({node.slice[0] : node.value})
        return Slice(node.wire, node.slice, frame)

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
