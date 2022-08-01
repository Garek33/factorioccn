from distutils.log import error
from typing import Mapping, Sequence
from unicodedata import name

from factorioccn.model.combinators import Circuit, Frame, Wire

class UnexpectedSignalError(Exception):
    def __init__(self, wire : str, actual : Frame, expected : Frame, tick : int, test : str):
        self.test = test
        self.wire = wire
        self.actual = actual
        self.expected = expected
        self.tick = tick

    def __str__(self) -> str:
        return f'unexpected signal in {self.test} at {self.tick}\n\texpected: {self.expected}\n\tactual:   {self.actual}'


class Tick:
    def __init__(self, tick : int, expected : Mapping[str,Frame], sets : Mapping[str,Frame]):
        self._expected = expected
        self._sets = sets
        self.tick = tick

    def execute(self, wires : Mapping[str, Wire], *errorargs):
        for w, f in self._expected.items():
            if wires[w].signals != f:
                raise UnexpectedSignalError(w, wires[w].signals, f, self.tick, *errorargs)
        for w, f in self._sets.items():
            wires[w].signals = f
            

class Test:
    def __init__(self, name : str, circuit : Circuit, ticks : Sequence[Tick]):
        self._name = name
        self._circuit = circuit
        self._ticks = ticks
    
    def run(self):
        t = 0
        for w in self._circuit.wires.values():
            w.signals += Frame()
        for tick in self._ticks:
            self._circuit.tick(tick.tick - t)
            tick.execute(self._circuit.wires, self._name)