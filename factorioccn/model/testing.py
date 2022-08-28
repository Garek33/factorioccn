from collections.abc import MutableMapping, Mapping, Sequence
from dataclasses import dataclass
from functools import reduce

from model.core import Frame, Wire


@dataclass
class SignalTest:
    """Represents testing an actual signal against an expectation"""
    wire: str
    stype: str
    expected: int
    actual: int

    def is_success(self) -> bool:
        """checks and returns whether the signal fulfills the expectation"""
        return self.expected == self.actual

    def __str__(self) -> str:
        return f'{self.wire}[{self.stype}]: expected {self.expected}, actual {self.actual}'


@dataclass
class TestOperation:
    """base class for set and expect operations in circuit testing.
    Operates on a single ``wire`` and a ``Frame`` of ``values``."""
    wire: str
    values: Frame

    # noinspection PyArgumentList
    def copy(self):
        """Create a copy of the actual TestOperation (i.e. the correct subclass)"""
        cls = type(self)
        return cls(self.wire, self.values.copy())


class TestExpects(TestOperation):
    """Test the specified ``wire`` against the ``values``."""
    def test(self, wires: Mapping[str, Wire]) -> Sequence[SignalTest]:
        """Test the specified ``wire`` against the ``values``.

        :param wires: All potentially relevant wires
        :return: The resulting set of ``SignalTest``s
        """
        wire = wires[self.wire]
        return [SignalTest(self.wire, stype, self.values[stype], wire.signals[stype]) for stype in self.values]


class TestSets(TestOperation):
    """Add the contained ``values`` to the specified ``wire``"""
    def set(self, wires: Mapping[str, Wire]) -> None:
        """Add the contained ``values`` to the specified ``wire``.

        :param wires: All potentially relevant wires
        """
        wires[self.wire].signals += self.values


class WrongSignalError(Exception):
    """Exception raised if a test fails with a mismatching or missing signal"""
    def __init__(self, results: Sequence[SignalTest], tick: int, test: str):
        self.test = test
        self.tick = tick
        self.results = results

    def __str__(self) -> str:
        return reduce((lambda acc, r: acc + f'\t{r}'), self.results,
                      f'unexpected signals in {self.test}:{self.tick}:\n')


class Tick:
    """a specific, non-empty tick of a circuit test"""
    def __init__(self, tick: int, expected: Sequence[TestExpects], sets: Sequence[TestSets]):
        """Create a test tick.

        :param tick: when this tick should be executed
        :param expected: ``TestExpects`` to check
        :param sets: ``TestSets`` to apply
        """
        self._expected: Sequence[TestExpects] = expected
        self._sets: Sequence[TestSets] = sets
        self.tick = tick

    def execute(self, wires: MutableMapping[str, Wire], *errorargs) -> None:
        """Apply this tick to the given set of wires.

        :param wires: wires to check and write to
        :param errorargs: passthrough for additional info to any WrongSignalError raised

        :raises WrongSignalError: if a check fails
        """
        tests = []
        for s in self._expected:
            tests += s.test(wires)
        failed = [t for t in tests if not t.is_success()]
        if len(failed) > 0:
            raise WrongSignalError(failed, self.tick, *errorargs)
        for s in self._sets:
            s.set(wires)


