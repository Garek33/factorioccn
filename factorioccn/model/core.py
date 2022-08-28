from collections import UserDict
from collections.abc import MutableSequence


class Frame(UserDict[str, int]):
    """represents a 'frame' of signals, e.g. the signals carried on a wire in a single tick

    This extends UserDict to create a MutableMapping[str,int] that simulates signal behaviour.
    Specifically, Frames can be added, and return 0 for a missing key.
    """

    def __iadd__(self, other):
        for key in list(other):
            if key not in self.keys():
                self[key] = 0
            self[key] += other[key]
        return self

    def __getitem__(self, key: str):
        """return self[key] or 0 if key not in self"""
        if key not in self.keys():
            return 0
        return super().__getitem__(key)


class Wire:
    """simulates a wire connecting multiple circuit elements.

    :var self.signals: the signals output from ``self.inputs`` or input by e.g. test simulation in the last tick
    :var self.inputs: the combinators which output to this wire, i.e. its inputs
    :var self.outputs: the combinators which use this wire as input, i.e. this wires outputs
    """

    def __init__(self):
        self.signals = Frame()
        """the signals output from ``self.inputs`` or input by e.g. test simulation in the last tick"""
        from model.combinators import Combinator  # local import to avoid cyclic dependency
        self.inputs: MutableSequence[Combinator] = []
        """the combinators which output to this wire, i.e. its inputs"""
        self.outputs: MutableSequence[Combinator] = []
        """the combinators which use this wire as input, i.e. this wires outputs"""

    def tick(self):
        """The wires half of tick simulation: write signals to outputs and then clear them"""
        for combinator in self.outputs:
            combinator.input += self.signals
        self.signals.clear()
