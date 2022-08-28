from importlib import resources

from tatsu import compile
from tatsu.semantics import ModelBuilderSemantics

from factorioccn.parser.walker import Walker
from model.toplevel import Circuit

with resources.open_text('factorioccn.parser', 'grammar.ebnf') as grammar_file:
    _grammar = grammar_file.read()
_parser = compile(_grammar, semantics=ModelBuilderSemantics())


def parse(input: str) -> Circuit:
    """parse fccn code into a simulation object.

    :param input: the code to parse as a string
    :return: the resulting circuit
    """
    model = _parser.parse(input)
    # noinspection PyShadowingNames
    walker = Walker()
    return walker.walk(model)
