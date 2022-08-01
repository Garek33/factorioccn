from typing import Sequence
from factorioccn.model.combinators import Circuit, Wire
from factorioccn.model.testing import Test, Tick

class CircuitBuilder:
    def __init__(self):
        self.circuit = Circuit()
        self.tests : list[Test] = []

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

    def addTest(self, name : str, ticks : Sequence[Tick]):
        self.tests.append(Test(name, self.circuit, ticks))

    def finalize(self):
        for test in self.tests:
            test.run()
        return self.circuit