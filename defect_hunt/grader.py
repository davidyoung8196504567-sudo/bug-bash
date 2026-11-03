"""Score a model's bug-finding tests against a task.

The rule: a test file earns credit only if it PASSES on the reference
implementation (it encodes correct behaviour) and FAILS on a mutant (it
detects that bug). A test that fails on the reference is invalid and earns
nothing, which blocks trivial reward hacks like `assert False`.
"""
from dataclasses import dataclass, field

from defect_hunt.sandbox import run_tests
from defect_hunt.tasks import Task


@dataclass
class GradeResult:
    task: str
    valid: bool                 # passes on the reference implementation
    killed: list[str] = field(default_factory=list)
    survived: list[str] = field(default_factory=list)
    reference_output: str = ""

    @property
    def score(self) -> float:
        total = len(self.killed) + len(self.survived)
        return len(self.killed) / total if (self.valid and total) else 0.0


def grade(task: Task, candidate_tests: str) -> GradeResult:
    ref = run_tests(task.reference, candidate_tests)
    result = GradeResult(task=task.name, valid=ref.passed, reference_output=ref.output)
    if not ref.passed:
        return result
    for m in task.mutants:
        if run_tests(m.source, candidate_tests).passed:
            result.survived.append(m.mutant_id)
        else:
            result.killed.append(m.mutant_id)
    return result
