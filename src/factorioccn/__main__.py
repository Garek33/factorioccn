import sys
from pprint import pprint

from factorioccn.parser import parse

if __name__ == '__main__':
    with open(sys.argv[1]) as infile:
        instr = infile.read()

    circuit = parse(instr)
    circuit.run_tests()
    pprint(circuit.wires)
    pprint(circuit.combinators)
