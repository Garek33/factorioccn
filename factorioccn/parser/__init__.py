from importlib import resources

from tatsu import compile

from factorioccn.parser.model import fccnModelBuilderSemantics
from factorioccn.parser.walker import Walker

with resources.open_text('factorioccn.parser', 'grammar.ebnf') as gfile:
    _grammar = gfile.read()
_parser = compile(_grammar, semantics=fccnModelBuilderSemantics())


def parse(input):
    model = _parser.parse(input)
    walker = Walker()
    return walker.walk(model)
