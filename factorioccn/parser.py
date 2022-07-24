from tatsu import parse

_grammar = '''
    @@grammar :: fccn
    @@whitespace :: /[\t ]+/
    @@eol_comments :: /#.*?$/

    start = '\\n'.{statement} $;
    statement = wireset '->' combinator '->' wireset 
                | () ;
    wireset = identifier [',' identifier] ;
    combinator = decider | arithmetic ;

    decider = argument logiop argument ':' deciderout ;
    deciderout = identifier ['(1)'] ;
    logiop = '>' | '>=' | '=' | '!=' | '<=' | '<' ;

    arithmetic = identifier '=' argument arthop argument ;
    arthop = '+' | '-' | '*' | '/' | '%' | '>>' | '<<' ;

    argument = identifier | number ;

    @name
    identifier = /[a-zA-Z_][0-9a-zA-Z_]*/ ;
    number = /[0-9]+/ ;
'''

if __name__ == '__main__':
    import sys
    import pprint
    
    with open(sys.argv[1]) as infile:
        instr = infile.read()

    ast = parse(_grammar, instr)
    pprint.pprint(ast, indent=2, width=200)
