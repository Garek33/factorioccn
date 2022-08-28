import sys
from pprint import pprint

from factorioccn.parser import _parser
from factorioccn.parser import parse

if __name__ == '__main__':
    with open(sys.argv[1]) as infile:
        instr = infile.read()

    model = _parser.parse(instr)
    pprint(model.lines[0].__class__)

    circuit = parse(instr)
    pprint(circuit.wires)
    pprint(circuit.combinators)
