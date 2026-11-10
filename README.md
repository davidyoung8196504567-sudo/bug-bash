# bug-bash

An environment for measuring, and eventually training, how well language
models find bugs in code against a written specification.

(Not related to the Bash shell. A *bug bash* is a software testing tradition:
the team spends a session trying to break the product, and whoever finds the
most real bugs wins. This project runs the same contest with language models
as the participants.)

**Status:** Phase 0, under active development. See [PLAN.md](PLAN.md) for the
timeline and [JOURNAL.md](JOURNAL.md) for the daily research log.
PDF copies of the plan and the ivrsim design are in [docs/pdf/](docs/pdf/), rebuilt
automatically whenever either changes.

## The idea

A model is given a task specification and an implementation that may contain
a bug. It must write tests that expose the bug. Scoring is automatic and needs
no human or LLM judge:

> A test earns credit only if it **passes on the correct implementation** and
> **fails on the buggy one**.

This is the standard a QA engineer applies to a bug report: it is not a bug
until there is a reproducible case, and the case has to be right about what
correct behaviour is. The rule also blocks the obvious reward hacks: a test
that always fails (`assert False`) fails on the correct code too and scores
zero.

## How it works

1. **Tasks** (`tasks/<name>/`): a `spec.md`, a correct `reference.py`, and
   `hidden_tests.py` that the model never sees.
2. **Bug injection** (`bugbash/mutate.py`): single-change mutants of the
   reference (swapped comparisons, off-by-one constants, flipped boolean logic).
3. **Mutant validation** (`bugbash/tasks.py`): a mutant is kept only if
   the hidden tests detect it. Rejected mutants are reviewed by hand, since
   they are either harmless or a gap in the hidden tests.
4. **Grading** (`bugbash/grader.py`): candidate tests must pass on the
   reference; the score is the fraction of mutants they detect.

## Quick start

```bash
pip install -e ".[dev]"
python -m bugbash.cli list
python -m bugbash.cli mutants business_hours
python -m bugbash.cli grade business_hours path/to/your_tests.py
python -m pytest tests
```

Candidate tests import the code under test as `impl`, for example
`from impl import is_open`.

## Guards

Everything in this repository is fictitious, and four guards keep it that way
(design: [IVRSIM_DESIGN.md](IVRSIM_DESIGN.md), section 6). They run in CI, and
as a pre-commit hook once you install it in your clone:

```bash
git config core.hooksPath tools/hooks
python tools/guards.py        # run them by hand over the whole tree
```

Names that must never be published go in `.guards-local.txt`, one per line.
Git ignores that file, and the guards refuse any commit that contains one of
its terms.

## Safety note

Phase 0 runs candidate tests in a subprocess with a timeout only. Do not
grade untrusted model output until the Docker sandbox (Phase 2) is in place.

## Author and tools

David Young. MEng Computer Engineering (thesis: Fuzzy ARTMAP neural network
speech recognition), 25+ years in software verification. Built with Claude
Code as a development partner; design decisions, task authoring and analysis
are my own.
