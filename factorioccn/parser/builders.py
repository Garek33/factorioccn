from factorioccn.model import BinaryCombinator, Circuit, Wire

class CircuitBuilder:
    def __init__(self):
        self.circuit = Circuit()

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