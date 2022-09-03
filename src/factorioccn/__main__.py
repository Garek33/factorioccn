import sys

from factorioccn.parser import parse


def main(infile_name):
    with open(infile_name) as infile:
        instr = infile.read()
    circuit = parse(instr)
    circuit.run_tests()


if __name__ == '__main__':  # pragma: no cover
    main(sys.argv[1])
