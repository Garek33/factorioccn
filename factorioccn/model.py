from functools import reduce
from typing import Iterable


class Frame:
    def __init__(self, initial = None):
        self._data = initial
        if self._data is None:
            self._data = {}

    def __iadd__(self, other):
        for key in list(other._data):
            if key not in self._data:
                self._data[key] = 0
            self._data[key] += other._data[key]
        return self

    def clear(self):
        self._data.clear()

    def __getitem__(self, key):
        if key not in self._data:
            return 0
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __str__(self): #pragma: no cover
        return str(self._data)


class Wire:
    def __init__(self):
        self.signals = Frame()
        self.inputs = []
        self.outputs = []
    
    def tick(self):
        for combinator in self.outputs:
            combinator.input += self.signals
        self.signals.clear()


class Combinator:
    def __init__(self, output_wires):
        self.input = Frame()
        self.output_wires = output_wires

    def tick(self):
        output = self.process(self.input)
        for wire in self.output_wires:
            wire.signals += output
        self.input.clear()


class BinaryCombinator(Combinator):
    def __init__(self, input_wires, left, right, output_wires):
        super().__init__(output_wires)
        self.input_wires = input_wires
        self.left = left
        self.right = right
        if(left == 'each'):
            self.select_inputs = lambda input: ({s : input[s] for s in input}, BinaryCombinator.process_arg(input, right))
        else:
            self.select_inputs = lambda input: ({left: input[left]}, BinaryCombinator.process_arg(input, right))
    
    def process_arg(input, key):
        try: #check for constant
            return int(key)
        except ValueError: #find it as a signal
            return input[key]


#TODO: handle wildcard signals!
class DeciderCombinator(BinaryCombinator):
    operations = {
        '>' : lambda a,b: a > b,
        '>=' : lambda a,b: a >= b,
        '=' : lambda a,b: a == b,
        '!=' : lambda a,b: a != b,
        '<=' : lambda a,b: a <= b,
        '<' : lambda a,b: a < b
    }

    def __init__(self, input_wires, left, op, right, output_signal, output_value, output_wires):
        super().__init__(input_wires, left, right, output_wires)
        self.op = op
        self.output_signal = output_signal
        self.output_value = output_value
        self._operation = DeciderCombinator.operations[op]
        self._shortcircuit = left == 'everything' or left not in ('anything', 'everything', 'each')
        if self._shortcircuit:
            self._aggpasses = lambda passes, cmp: passes and cmp
        elif left == 'anything':
            self._aggpasses = lambda passes, cmp: passes or cmp
        else:
            self._aggpasses = lambda _, __: True
        if self.output_signal == 'each':
            self._accsignal = lambda stype, rval, cmp: Frame({stype : rval}) if cmp else Frame()
        elif self.output_signal == 'everything':
            self._accsignal = lambda stype, rval, _: Frame({stype : rval})
        elif self.output_signal == 'anything':
            self._accsignal = lambda stype, rval, cmp: Frame({stype : rval}) if cmp else Frame()
        elif left == 'each':
            self._accsignal = lambda __, rval, _: Frame({output_signal : rval})
        else:
            self._accsignal = lambda stype, rval, _: Frame({stype : rval}) if stype == output_signal else Frame()
        if self.left in ('everything', 'anything'):
            self.select_inputs = lambda input: ({s : input[s] for s in input if s != right}, BinaryCombinator.process_arg(input, right))
        if self.output_signal in ('each', 'anything'):
            self._select_iter = lambda _, left: left
        else:
            self._select_iter = lambda input, _: input._data

    def select_data(self, input):
        (left, right) = self.select_inputs(input)
        return (left, right, self._select_iter(input, left))
        
    def process(self, input):
        (left,right,iter) = self.select_data(input)
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
                break #TODO: proper ordering of signals!
        if passes:
            return output
        else:
            return Frame()


class ArithmeticCombinator(BinaryCombinator):
    operations = {
        '+' : lambda a,b: a + b,
        '-' : lambda a,b: a - b,
        '*' : lambda a,b: a * b,
        '/' : lambda a,b: a // b,
        '%' : lambda a,b: a % b,
        '**' : lambda a,b: a ** b,
        '<<' : lambda a,b: a << b,
        '>>' : lambda a,b: a >> b,
        '&' : lambda a,b: a & b,
        '|' : lambda a,b: a | b,
        '^' : lambda a,b: a ^ b,
    }

    def __init__(self, input_wires, left, op, right, output_signal, output_wires):
        super().__init__(input_wires, left, right, output_wires)
        self.op = op
        self.output_signal = output_signal
        self._operation = ArithmeticCombinator.operations[op]
        
    def process(self, input):
        (left,right) = self.select_inputs(input)
        intermediate = {x : self._operation(left[x],right) for x in left}
        if(self.output_signal == 'each'):
            return Frame(intermediate)
        else:
            return Frame({self.output_signal : reduce(lambda a, b: a+b, intermediate.values())})


class ConstantCombinator(Combinator):
    def __init__(self, signals, output_wires):
        super().__init__(output_wires)
        self.signals = signals
    
    def process(self, _):
        return self.signals


class Circuit:
    def __init__(self):
        self.wires = {}
        self.combinators = []

    def tick(self,n = 1):
        for i in range(n):
            for unused, wire in self.wires.items():
                wire.tick()
            for combinator in self.combinators:
                combinator.tick()
    
    def dump(self): #pragma: no cover
        for key in self.wires:
            print(f'{key}: {self.wires[key].signals}')