from tatsu import compile
from importlib import resources

with resources.open_text('factorioccn.parser','grammar.ebnf') as gfile:
    _grammar = gfile.read()

parser = compile(_grammar)
