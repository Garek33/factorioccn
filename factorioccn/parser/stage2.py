from tatsu.walkers import PreOrderWalker

from factorioccn.model import Circuit, Wire, DeciderCombinator, ArithmeticCombinator

class FCCNWalker(PreOrderWalker):
    def __init__(self):
        self.circuit = Circuit()

    def walk_Statement(self, node):
        node.action.input = node.input
        node.action.output = node.output

    def walk_Decider(self, node):
        inputs = self.processWires(node.input)
        outputs = self.processWires(node.output)
        output_signal = node.result.signal
        output_value = node.result.value
        if output_value is not None:
            output_value = 1
        combinator = DeciderCombinator(inputs, node.left, node.op, node.right, output_signal, output_value, outputs)
        self.registerCombinator(combinator)
        
    def walk_Arithmetic(self, node):
        inputs = self.processWires(node.input)
        outputs = self.processWires(node.output)
        combinator = ArithmeticCombinator(inputs, node.left, node.op, node.right, node.result, outputs)
        self.registerCombinator(combinator)

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