from collections.abc import Sequence
from functools import reduce
from typing import Any

from model.core import Frame, Wire


class Combinator:
    """base class for all combinators

    This already handles input from wires and most of the tick simulation.
    Subclasses are required to implement ``process``.
    """
    def __init__(self, output_wires: Sequence[Wire]):
        self.input = Frame()
        """input signals, written by ``Wire.tick``"""
        self.output_wires = output_wires
        """wires to which ``Combinator.tick`` outputs"""

    def tick(self):
        """The combinators half of circuit simulation."""
        output = self.process(self.input)
        for wire in self.output_wires:
            wire.signals += output
        self.input.clear()

    def process(self, input: Frame):
        """Abstract method which does the actual input processing.

        :param input: the current input signals
        :returns: a Frame containing the resulting signals to output

        :raise NotImplementedError: if not overwritten in a derived class
        """
        raise NotImplementedError("Combinator.process")


# noinspection PyAbstractClass
class BinaryCombinator(Combinator):
    """intermediate base for combinators implementing a binary operation.

    Binary operation means an operation with two operands, the first of which must be a signal from input,
    while the second one may be a signal or a constant.
    ``BinaryCombinator`` provides common handling of storing input and output wires, operand names,
    as well as the helpers ``select_inputs`` and ``process_arg``
    """
    def __init__(self, input_wires: Sequence[Wire], left: str, right: str, output_wires: Sequence[Wire]):
        """create a BinaryCombinator. This does not modify the given wires,
        adding the combinator to their inputs and outputs is the callers' responsibility.

        Currently, operands are handled as strings.
        TODO: implement classes for operands, considering signal-types, wildcards and constants
        :param input_wires: wires connected as an input to this combinator.
        :param left: left operand, this must be a signal type or wildcard
        :param right: right operand, this may be a signal type, wildcard or integer constant
        :param output_wires: wires connected as an output to this combinator, see ``Combinator.output_wires``
        """
        super().__init__(output_wires)
        self.input_wires = input_wires
        self.left = left
        self.right = right
        if left == 'each':
            self.select_inputs = lambda input: (
                {s: input[s] for s in input}, BinaryCombinator.process_arg(input, right))
        else:
            self.select_inputs = lambda input: ({left: input[left]}, BinaryCombinator.process_arg(input, right))
            """extract arguments from an input frame according to ``left`` and ``right``
            
            :param input: ``Frame`` of input signals
            :returns: a tuple containing the left and right argument extracted from input
            """

    @staticmethod
    def process_arg(input: Frame, arg: str) -> int:
        """Check if an argument is a constant, otherwise retrieve it from input.

        :param input: ``Frame`` of input signals
        :param arg: argument as given, maybe an integer constant or a key into ``input``
        :return: final argument value as an integer
        """
        try:  # check for constant
            return int(arg)
        except ValueError:  # find it as a signal
            return input[arg]


class DeciderCombinator(BinaryCombinator):
    """Simulate a decider combinator, that is a combinator performing certain logic operations."""
    operations = {
        '>': lambda a, b: a > b,
        '>=': lambda a, b: a >= b,
        '=': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
        '<=': lambda a, b: a <= b,
        '<': lambda a, b: a < b
    }

    def __init__(self, input_wires: Sequence[Wire], left: str, op: str, right: str,
                 output_signal: str, output_value: Any, output_wires: Sequence[Wire]):
        """create a decider combinator

        :param input_wires: wires connected as an input to this combinator, see ``BinaryCombinator.input_wires``
        :param left: left operand, this must be a signal type or wildcard
        :param op: logic operation, one of '>', '>=', '=', '!=', '<=', '<'
        :param right: right operand, this may be a signal type, wildcard or integer constant
        :param output_signal: signal type or wildcard to output
        :param output_value: either 1 or None. The latter acts as a flag for outputting the input value
        :param output_wires: wires connected as an output to this combinator, see ``Combinator.output_wires``
        """
        super().__init__(input_wires, left, right, output_wires)
        self.op = op
        self.output_signal = output_signal
        self.output_value = output_value
        self._operation = DeciderCombinator.operations[op]
        self._shortcircuit = left == 'everything' or left not in ('anything', 'everything', 'each')
        self._determine_aggpasses(left)
        self._determine_accsignal(left, output_signal)
        self._determine_dataselects(right)

    def _determine_aggpasses(self, left):
        if self._shortcircuit:
            self._aggpasses = lambda passes, cmp: passes and cmp
        elif left == 'anything':
            self._aggpasses = lambda passes, cmp: passes or cmp
        else:
            self._aggpasses = lambda _, __: True

    def _determine_accsignal(self, left, output_signal):
        if self.output_signal == 'each':
            self._accsignal = lambda stype, rval, cmp: Frame({stype: rval}) if cmp else Frame()
        elif self.output_signal == 'everything':
            self._accsignal = lambda stype, rval, _: Frame({stype: rval})
        elif self.output_signal == 'anything':
            self._accsignal = lambda stype, rval, cmp: Frame({stype: rval}) if cmp else Frame()
        elif left == 'each':
            self._accsignal = lambda __, rval, cmp: Frame({output_signal: rval}) if cmp else Frame()
        else:
            self._accsignal = lambda stype, rval, _: Frame({stype: rval}) if stype == output_signal else Frame()

    def _determine_dataselects(self, right):
        if self.left in ('everything', 'anything'):
            self.select_inputs = lambda input: (
                {s: input[s] for s in input if s != right}, BinaryCombinator.process_arg(input, right))
        if self.output_signal in ('each', 'anything'):
            self._select_iter = lambda _, left: left
        elif self.output_signal == 'everything':
            self._select_iter = lambda input, _: input
        else:
            self._select_iter = lambda input, left: {**left, self.output_signal: input[self.output_signal]}

    def _select_data(self, input):
        (left, right) = self.select_inputs(input)
        return left, right, self._select_iter(input, left)

    def process(self, input):
        (left, right, iter) = self._select_data(input)
        output = Frame()
        passes = True
        for stype, value in iter.items():
            if stype in left.keys():
                cmp = self._operation(value, right)
                passes = self._aggpasses(passes, cmp)
                if not passes and self._shortcircuit:
                    break
            else:
                cmp = True
            rval = value if self.output_value is None else self.output_value
            output += self._accsignal(stype, rval, cmp)
            if self.output_signal == 'anything' and cmp:
                break  # TODO: proper ordering of signals!
        if passes:
            return output
        else:
            return Frame()


class ArithmeticCombinator(BinaryCombinator):
    """simulate an arithmetic combinator"""
    operations = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a // b,
        '%': lambda a, b: a % b,
        '**': lambda a, b: a ** b,
        '<<': lambda a, b: a << b,
        '>>': lambda a, b: a >> b,
        '&': lambda a, b: a & b,
        '|': lambda a, b: a | b,
        '^': lambda a, b: a ^ b,
    }

    def __init__(self, input_wires: Sequence[Wire], left: str, op: str, right: str,
                 output_signal: str, output_wires: Sequence[Wire]):
        """create a decider combinator

        :param input_wires: wires connected as an input to this combinator, see ``BinaryCombinator.input_wires``
        :param left: left operand, this must be a signal type or wildcard
        :param op: logic operation, one of '+', '-', '*', '/', '%', '**' (power), '<<', '>>', '&', '|', '^'
        :param right: right operand, this may be a signal type, wildcard or integer constant
        :param output_signal: signal type or wildcard to output
        :param output_wires: wires connected as an output to this combinator, see ``Combinator.output_wires``
        """
        super().__init__(input_wires, left, right, output_wires)
        self.op = op
        self.output_signal = output_signal
        self._operation = ArithmeticCombinator.operations[op]

    def process(self, input):
        (left, right) = self.select_inputs(input)
        intermediate = {x: self._operation(left[x], right) for x in left}
        if self.output_signal == 'each':
            return Frame(intermediate)
        else:
            return Frame({self.output_signal: reduce(lambda a, b: a + b, intermediate.values())})


class ConstantCombinator(Combinator):
    """simulate a constant combinator, that is a combinator outputting a constant frame of signals."""
    def __init__(self, signals: Frame, output_wires: Sequence[Wire]):
        """create a constant combinator

        :param signals: ``Frame`` of signals to output
        :param output_wires: wires to output to, see ``Combinator.output_wires``
        """
        super().__init__(output_wires)
        self.signals = signals

    def process(self, _):
        return self.signals


