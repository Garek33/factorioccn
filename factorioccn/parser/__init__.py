from tatsu import compile
from importlib import resources
from factorioccn.parser.model import fccnModelBuilderSemantics

with resources.open_text('factorioccn.parser','grammar.ebnf') as gfile:
    _grammar = gfile.read()

parser = compile(_grammar, semantics=fccnModelBuilderSemantics())
