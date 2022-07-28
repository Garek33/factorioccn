# Factorio Circuit Combinator Notation - factorioccn

The Factorio Circuit Combinator Notation (factorioccn or fccn for short) is a language designed for developing and testing combinator circuits for the game Factorio.
factiorioccn also is a python module which implements this language. It uses TatSu for parsing and factorio-draftsman for some validation and blueprint generation.

## Design goals

* Exact mapping of Factorio circuit network and combinator mechanics to code
    * Maybe: placeholders for other circuit-connected entities with limited functionality
* Tests alongside circuit definitions
* Support code reusability
    * template blocks which are parametrized sub-circuits
    * compile-time flow control like loops or conditions
* Shorthand notation for common patterns, e.g. artifical delays, multiple operations on a single signal and wire
* Standalone factorioccn executable can run tests and generate blueprints
* factorioccn as a library alongside factorio-draftsman for experimentation and complex blueprint generation

## Current features

* parse simple circuits to a simulation model which can be run from python

## Roadmap

This is roughly in expected order of implementation, but not a strict schedule in any way, shape or form.

* comprehensive unittests
* wildcard signals
* constant combinators
* run test code
* simple placement algorithm
* proper standalone executable for tests and blueprint generation
* compile-time arithmetic expressions
* shorthand for multiple arithmetic operations on a single signal and wire
* templates
* import other fccn files
* compile-time flow control
* better placement algorithm (simulated annealing?)
* host functions: call predefined python functions from fccn
    * maybe user-defined in fccn via embedded python?
* connect other entities beside combinators and poles
