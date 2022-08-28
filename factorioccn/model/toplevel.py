"""Classes that represent some constructs on the top level of a fccn file,
most of which may be returned as a parsing result"""
from collections.abc import Sequence, MutableMapping, MutableSequence

from model.combinators import Combinator
from model.core import Wire, Frame
from model.testing import Tick


class Circuit:
    """A combinator circuit and its associated tests"""
    def __init__(self):
        self.wires: MutableMapping[str, Wire] = {}
        self.combinators: MutableSequence[Combinator] = []
        self.tests: Sequence[Test] = []

    def tick(self, n: int = 1) -> None:
        """simulate the circuit for n ticks.

        :param n: amount of ticks to simulate
        """
        for i in range(n):
            for wire in self.wires.values():
                wire.tick()
            for combinator in self.combinators:
                combinator.tick()

    def dump(self):  # pragma: no cover
        for key in self.wires:
            print(f'{key}: {self.wires[key].signals}')


class Test:
    """A full test run for a specific ``Circuit``"""
    def __init__(self, name: str, circuit: Circuit, ticks: Sequence[Tick]):
        """Create a test for a specific ``Circuit``.

        :param name: name of the test for output purposes
        :param circuit: ``Circuit`` to test
        :param ticks: Sequence of ticks to apply to the circuit during simulation
        """
        self._name = name
        self._circuit = circuit
        self._ticks = ticks

    def run(self):
        """simulate the circuit while applying the test ticks at the appropriate tick"""
        t = 0
        for w in self._circuit.wires.values():
            w.signals = Frame()
        for tick in self._ticks:
            delta = tick.tick - t
            t += delta
            self._circuit.tick(delta)
            tick.execute(self._circuit.wires, self._name)
