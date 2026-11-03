"""Command line entry point.

    python -m defect_hunt.cli mutants business_hours
    python -m defect_hunt.cli grade business_hours path/to/candidate_tests.py
"""
import argparse
from pathlib import Path

from defect_hunt.grader import grade
from defect_hunt.tasks import build_mutants, list_tasks, load_task


def main(argv=None):
    parser = argparse.ArgumentParser(prog="defect_hunt")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p_mut = sub.add_parser("mutants")
    p_mut.add_argument("task")
    p_grade = sub.add_parser("grade")
    p_grade.add_argument("task")
    p_grade.add_argument("tests", type=Path)
    args = parser.parse_args(argv)

    if args.cmd == "list":
        print("\n".join(list_tasks()))
        return
    task = build_mutants(load_task(args.task))
    if args.cmd == "mutants":
        print(f"{task.name}: {len(task.mutants)} kept, {len(task.rejected)} rejected")
        for m in task.mutants:
            print(f"  KEEP   {m.mutant_id} line {m.line:3d} {m.operator:17s} {m.description}")
        for m in task.rejected:
            print(f"  REJECT {m.mutant_id} line {m.line:3d} {m.operator:17s} {m.description}")
    elif args.cmd == "grade":
        r = grade(task, args.tests.read_text(encoding="utf-8"))
        if not r.valid:
            print("INVALID: candidate tests fail on the reference implementation")
            print(r.reference_output[-2000:])
            return
        print(f"{task.name}: killed {len(r.killed)}/{len(r.killed) + len(r.survived)} "
              f"mutants, score {r.score:.2f}")
        for mid in r.survived:
            print(f"  survived {mid}")


if __name__ == "__main__":
    main()
