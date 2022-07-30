from tatsu.walkers import DepthFirstWalker

from factorioccn.model import Circuit, Wire, Frame, DeciderCombinator, ArithmeticCombinator, ConstantCombinator

class FCCNWalker(DepthFirstWalker):
    def __init__(self):
        self.circuit = Circuit()

    def walk_Combinatorstmt(self, node, children):
        parts = {x[0]:x[1] for x in children}
        input = parts[node.input] if node.input is not None else []
        combinator = parts[node.action](input, parts[node.output])
        self.registerCombinator(combinator)

    def walk_Wires(self, node, _):
        return (node,self.processWires(node.wires))

    def walk_Decider(self, node, _):
        output_signal = node.result.signal
        output_value = node.result.value
        if output_value is not None: #TODO: raise error
            output_value = 1
        return (node, lambda inputs, outputs: DeciderCombinator(inputs, node.left, node.op, node.right, output_signal, output_value, outputs))
        
    def walk_Arithmetic(self, node, _):
        return (node, lambda inputs, outputs: ArithmeticCombinator(inputs, node.left, node.op, node.right, node.result, outputs))

    def walk_ConstantCombinator(self, node, children):
        #TODO: validate no input
        return (node, lambda _, outputs: ConstantCombinator(children[0], outputs))

    def walk_Constframe(self, node, _):
        return Frame({s.type : s.value for s in node.signals})

    def processWires(self, wireset):
        for wire in wireset:
            if wire not in self.circuit.wires:
                self.circuit.wires[wire] = Wire()
        return [self.circuit.wires[w] for w in wireset]
    
    def registerCombinator(self, combinator):
        self.circuit.combinators.append(combinator)
        for wire in combinator.input_wires:
            wire.outputs.append(combinator)
        for wire in combinator.output_wires:
            wire.inputs.append(combinator)