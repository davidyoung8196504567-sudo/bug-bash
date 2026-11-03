"""Tests for the environment itself: the mutator, the task loader and the grader."""
import pytest

from bugbash.grader import grade
from bugbash.mutate import generate_mutants
from bugbash.tasks import build_mutants, list_tasks, load_task

SAMPLE = "def f(a, b):\n    return a < b and not a == 0\n"


def test_every_mutant_differs_from_original_and_parses():
    import ast
    original = ast.unparse(ast.parse(SAMPLE))
    mutants = generate_mutants(SAMPLE)
    assert mutants
    for m in mutants:
        ast.parse(m.source)
        assert m.source != original


def test_operators_cover_compare_boolop_not_and_constants():
    ops = {m.operator for m in generate_mutants(SAMPLE)}
    assert {"compare_swap", "boolop_swap", "drop_not", "const_off_by_one"} <= ops


def test_drop_not_removes_only_the_targeted_not():
    src = "def f(a, b):\n    return (not a, not b)\n"
    drops = [m for m in generate_mutants(src) if m.operator == "drop_not"]
    assert len(drops) == 2
    assert {d.source.count("not ") for d in drops} == {1}
    assert len({d.source for d in drops}) == 2


def test_mutant_ids_are_unique():
    ids = [m.mutant_id for m in generate_mutants(SAMPLE, "t")]
    assert len(ids) == len(set(ids))


@pytest.fixture(scope="module")
def business_hours():
    return build_mutants(load_task("business_hours"))


def test_tasks_are_discovered():
    assert "business_hours" in list_tasks()


def test_business_hours_has_validated_mutants(business_hours):
    assert len(business_hours.mutants) >= 10


def test_always_failing_tests_are_invalid(business_hours):
    r = grade(business_hours, "def test_x():\n    assert False\n")
    assert not r.valid
    assert r.score == 0.0


def test_hidden_tests_kill_every_kept_mutant(business_hours):
    r = grade(business_hours, business_hours.hidden_tests)
    assert r.valid
    assert r.score == 1.0


def test_weak_tests_get_partial_credit(business_hours):
    weak = (
        "import datetime as dt\n"
        "from impl import is_open\n"
        "def test_midday():\n"
        "    assert is_open(dt.datetime(2026, 11, 2, 12, 0), set())\n"
    )
    r = grade(business_hours, weak)
    assert r.valid
    assert 0.0 < r.score < 1.0
