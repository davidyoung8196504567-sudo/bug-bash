"""Load tasks and build the validated mutant set for each one."""
from dataclasses import dataclass, field
from pathlib import Path

from defect_hunt.mutate import Mutant, generate_mutants
from defect_hunt.sandbox import run_tests

TASKS_DIR = Path(__file__).resolve().parent.parent / "tasks"


@dataclass
class Task:
    name: str
    spec: str
    reference: str
    hidden_tests: str
    mutants: list[Mutant] = field(default_factory=list)
    rejected: list[Mutant] = field(default_factory=list)


def load_task(name: str) -> Task:
    d = TASKS_DIR / name
    return Task(
        name=name,
        spec=(d / "spec.md").read_text(encoding="utf-8"),
        reference=(d / "reference.py").read_text(encoding="utf-8"),
        hidden_tests=(d / "hidden_tests.py").read_text(encoding="utf-8"),
    )


def list_tasks() -> list[str]:
    return sorted(p.name for p in TASKS_DIR.iterdir() if (p / "spec.md").exists())


def build_mutants(task: Task) -> Task:
    """Keep only mutants the hidden tests detect (behaviour-changing bugs).

    Mutants the hidden tests miss are either equivalent (no observable change)
    or expose a gap in the hidden tests; both are recorded in task.rejected
    for review rather than silently dropped.
    """
    if not run_tests(task.reference, task.hidden_tests).passed:
        raise ValueError(f"{task.name}: reference fails its own hidden tests")
    for m in generate_mutants(task.reference, task.name):
        if run_tests(m.source, task.hidden_tests).passed:
            task.rejected.append(m)
        else:
            task.mutants.append(m)
    return task
