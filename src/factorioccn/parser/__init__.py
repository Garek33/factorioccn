from importlib import resources

from tatsu import compile
from tatsu.semantics import ModelBuilderSemantics

from factorioccn.model.toplevel import Circuit
from factorioccn.parser.builders import CircuitBuilder

with resources.open_text('factorioccn.parser', 'grammar.ebnf') as grammar_file:
    _grammar = grammar_file.read()
_parser = compile(_grammar, semantics=ModelBuilderSemantics())


def parse(input: str) -> Circuit:
    """parse fccn code into a simulation object.

    :param input: the code to parse as a string
    :return: the resulting circuit
    """
    model = _parser.parse(input)
    walker = CircuitBuilder()
    return walker.walk(model)
