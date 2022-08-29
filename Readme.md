# Factorio Circuit Combinator Notation - factorioccn

The Factorio Circuit Combinator Notation (factorioccn or fccn for short) is a language designed for developing and testing combinator circuits for the game [Factorio](https://factorio.com).
factorioccn also is a python module which implements this language. It uses [TatSu](https://tatsu.readthedocs.io) for parsing and [factorio-draftsman](https://github.com/redruin1/factorio-draftsman) for some validation and blueprint generation.

WARNING: THIS IS VERY PRE-ALPHA. There will be breaking changes without notice!

## Installation and usage

TBD. This is not yet available other than source distribution, and there is no proper CLI yet.

## Introductory example

For an explanation of factorios circuit network and combinator mechanics, see also [the factorio wiki](https://wiki.factorio.com/Circuit_network). TODO: refer to fccn docs.

Let's say you want to create a controller for a power plant, that enables steam generation when the amount of steam read from a tank gets low, and disables it again on high steam.
We can use a latch, i.e. a bistable circuit that can be used as one-bit memory, for that. A basic RS-Latch can be expressed in fccn like:
```
in, loop -> S > R : S=1 -> loop, out
```
A basic combinator statement starts with the input wires, then an expression defining the combinator, and finally the output wires.
The combinator here is a decider combinator, which outputs a 1 on the `S` signal if in it's input `S` is greater than `R`.
You may notice that one of the outputs, `loop`, loops back to the input. Keep in mind that a combinators output changes one tick after the input.

So this starts out with no signals on `loop`. If `in` has `S > R` (e.g. `S` is 1 and no `R`), the combinator starts outputting a 1 on `S`.
Then we have a stable output of `S = 1`, even with no input. When `in` contains `R > S-1` (e.g. `R` is 1 and no `S`), this resets the latch to its empty state.

But we still need to generate the `S` and `R` signals. As mentioned previously, let's assume our input is the amount of steam from a tank:
```
io -> steam < 10000 : S=1 -> latch_in
io -> steam > 20000 : R=1 -> latch_in
latch_in, loop -> S > R : S=1 -> loop, io
```
The example also changed to having a single wire connection, `io` to the actual tank and plant. 
We assume that steam generation gets enabled by `S=1` on `io` outside the current circuit.

While this simple example is easy to think through, we generally don't want to draft a circuit and put it into our factory immediately, i.e. 'test it in production'.
Because testing circuits inside factorio is cumbersome, requiring either mods or even more circuits, fccn provides facilities for defining tests alongside the circuit definition:
```
io -> steam < 10000 : S=1 -> latch_in
io -> steam > 20000 : R=1 -> latch_in
latch_in, loop -> S > R : S=1 -> loop, io

test setAndReset {
    0: io += {steam:12000}, for 3 io =~ {S:0}  
    #on tick 0, start with 'enough' steam. Also check for the next 3 ticks (including tick 0) that S doesn't get set. 
    #This considers the propagation delay of 2 through the circuit (it should also output nothing until the initial input has propagated)
    1: io += {steam:500}            #on tick 1, send a single blip of not enough steam
    2: for 5 io += {steam:13000}    #for ticks 2 to 6, send an in between amount of steam
    3: for 6 io =~ {S:1}            #after propagation delay, we expect S=1 for ticks 3 to 8
    7: io += {steam:21000}          #send enough steam to reset the latch
    8: for 3 io += {steam:19000}    #inbetween amount til tick 10
    9: for 3 io =~ {S:0, R:0}       #expect S to be (and keep) reset, also check for R not leaking
}
```

## Design goals

* Exact mapping of Factorio circuit network and combinator mechanics to code
* Tests alongside circuit definitions
* Support reusable and concise code with e.g. circuit templates, compile-time flow control and support for multi-file projects
* Shorthand notation for common patterns, e.g. artificial delays, multiple operations on a single signal and wire
* Standalone factorioccn executable can run tests and generate blueprints
* factorioccn as a library alongside factorio-draftsman for experimentation and complex blueprint generation

## Current features

* parse simple circuits to a simulation model which can be run from python
    * decider and arithmetic combinators including a basic implementation of wildcard signals, as well as constant combinators
* define tests alongside the circuit definition, which are run automatically during compilation
    * currently, success is silent and errors simply raise python exceptions

## Roadmap

This is roughly in expected order of implementation, but not a strict schedule in any way, shape or form.

* (more) comprehensive unittests
* simple placement algorithm and blueprint output (the latter via draftsman for validation)
    * I'm currently thinking about using a greedy BFS. That's not as simple as possible, but otoh could handle a lot of circuits reasonably well.
* proper standalone executable / CLI for tests and blueprint generation
* more readable output
    * don't leak python stacktraces for fccn parsing, semantic and test errors
    * understandable basic, verbose and tracing output for compilation and test runs
* more input validation i.e. semantic errors
* a proper manual for fccn
* use draftsman in the validation/simulation process
    * validate signal names (with shorthands i.e. `S` for `signal-s` and `steam` for `fluid-steam`)
    * correct signal order for anything expressions
* shorthands
    * multiple combinators in a statement with anonymous wires in between for single-wire operation
    * multiple arithmetic operations on a single signal and wire as a single expression
* constant folding, i.e. compile-time arithmetic expressions
* templates
* import other fccn files
* compile-time flow control
* better placement algorithm (simulated annealing?)
* host functions: call predefined python functions from fccn
    * maybe user-defined in fccn via embedded python?
    * will be extensible when used as a python module
    * built-in: manage signal propagation/delay, enumerate signals, stack sizes, etc.
* connect other entities beside combinators and poles
