from dataclasses import dataclass
from functools import reduce
from typing import Mapping, Sequence

from factorioccn.model.combinators import Circuit, Frame, Wire

@dataclass
class Signalresult:
    wire: str
    stype: str
    expected: int
    actual: int

    def isSuccess(self):
        return self.expected == self.actual
    
    def __str__(self) -> str:
        return f'{self.wire}[{self.stype}]: expected {self.expected}, actual {self.actual}'


@dataclass
class TestOperation:
    wire: str
    values: Frame

    def copy(self):
        return self.__class__(self.wire, self.values.copy())
    

class TestExpects(TestOperation):
    def test(self, wires: Mapping[str, Wire]) -> Sequence[Signalresult]:
        wire = wires[self.wire]
        return [Signalresult(self.wire, stype, self.values[stype], wire.signals[stype]) for stype in self.values]

class TestSets(TestOperation):
    def set(self, wires: Mapping[str, Wire]):
        wires[self.wire].signals += self.values


class UnexpectedSignalError(Exception):
    def __init__(self, results : Sequence[Signalresult], tick : int, test : str):
        self.test = test
        self.tick = tick
        self.results = results

    def __str__(self) -> str:
        return reduce((lambda acc, r: acc + f'\t{r}'), self.results, f'unexpected signals in {self.test}:{self.tick}:\n')


class Tick:
    def __init__(self, tick : int, expected : Sequence[TestExpects], sets : Sequence[TestSets]):
        self._expected : Sequence[TestExpects] = expected
        self._sets : Sequence[TestSets] = sets
        self.tick = tick

    def execute(self, wires : Mapping[str, Wire], *errorargs):
        tests = []
        for s in self._expected:
            tests += s.test(wires)
        failed = [t for t in tests if not t.isSuccess()]
        if len(failed) > 0:
            raise UnexpectedSignalError(failed, self.tick, *errorargs)
        for s in self._sets:
            s.set(wires)
            

class Test:
    def __init__(self, name : str, circuit : Circuit, ticks : Sequence[Tick]):
        self._name = name
        self._circuit = circuit
        self._ticks = ticks
    
    def run(self):
        t = 0
        for w in self._circuit.wires.values():
            w.signals = Frame()
        for tick in self._ticks:
            delta = tick.tick - t
            t += delta
            self._circuit.tick(delta)
            tick.execute(self._circuit.wires, self._name)