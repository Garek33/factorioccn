from factorioccn.parser import parser

if __name__ == '__main__':
    import sys
    import pprint
    
    with open(sys.argv[1]) as infile:
        instr = infile.read()

    ast = parser.parse(instr)
    pprint.pprint(ast, indent=2, width=200)