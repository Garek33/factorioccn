from tatsu import compile
from importlib import resources
from factorioccn.parser.model import fccnModelBuilderSemantics
from factorioccn.parser.stage2 import FCCNWalker

with resources.open_text('factorioccn.parser','grammar.ebnf') as gfile:
    _grammar = gfile.read()
_parser = compile(_grammar, semantics=fccnModelBuilderSemantics())

def parse(input):
    model = _parser.parse(input)
    walker = FCCNWalker()
    return walker.walk(model)
