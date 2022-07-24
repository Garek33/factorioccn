class SignalSet:
    def __init__(self, initial = {}):
        self._data = initial

    def __iadd__(self, other):
        for key in list(other._data):
            if self._data[key] is None:
                self._data[key] = 0
            self._data[key] += other._data[key]

    def clear(self):
        self._data.clear()

    def __getitem__(self, key):
        val = self._data[key]
        if val is None: val = 0
        return val
    
    def determine_arg(self, key):
        try: #check for constant
            return int(key)
        else: #find it as a signal
            return self[key]


class Wire:
    def __init__(self):
        self.signals = SignalSet()
        self.inputs = {}
        self.outputs = {}
    
    def tick(self):
        for combinator in self.outputs:
            combinator.input += self.signals
        self.signals.clear()


class Combinator:
    def __init__(self, input_wires, output_wires):
        self.input_wires = input_wires
        self.input = SignalSet()
        self.output_wires = output_wires

    def tick(self):
        output = self.process(self.input)
        for wire in self.output_wires:
            wire.data += output
        self.input.clear()

#TODO: handle wildcard signals!
class DeciderCombinator(Combinator):
    operations = {
        '>' : lambda a,b: a > b,
        '>=' : lambda a,b: a >= b,
        '=' : lambda a,b: a = b,
        '!=' : lambda a,b: a != b,
        '<=' : lambda a,b: a <= b,
        '<' : lambda a,b: a < b
    }

    def __init__(self, input_wires, left, op, right, output_signal, output_value, output_wires):
        Combinator.__init__(self, input_wires, output_wires)
        self.op = op
        self.left = left
        self.right = right
        self.output_signal = output_signal
        self.output_value = output_value
        _operation = operations[op]
        if output_value is None:
            self._out = lambda input: input[output_signal]
        else:
            self._out = lambda input: SignalSet({output_signal : output_value})
        
    def process(input):
        left = input.determine_arg(self.left)
        right = input.determine_arg(self.right)
        return self._out(self._operation(left,right))


class ArithmeticCombinator(Combinator):
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
        Combinator.__init__(self, input_wires, output_wires)
        self.op = op
        self.left = left
        self.right = right
        self.output_signal = output_signal
        _operation = operations[op]
        
    def process(input):
        left = input.determine_arg(self.left)
        right = input.determine_arg(self.right)
        return SignalSet({output_signal : self._operation(left,right)})


class Circuit:
    def __init__(self, wires = {}, combinators = []):
        self.wires = wires
        self.combinators = combinators

    def tick(n = 1):
        for i in range(n):
            for wire in self.wires:
                wire.tick()
            for combinator in self.combinators:
                combinator.tick()