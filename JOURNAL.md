# Research Journal

Daily log for defect-hunt. One entry per working session, newest at the top.
Targets and phases are in [PLAN.md](PLAN.md).

Entry template:

```
## YYYY-MM-DD (Day N) | Phase X | ~H hours
**Goal:** what this session set out to do
**Done:** what actually got done
**Findings:** anything surprising, measured, or worth putting in the report
**Blockers / risks:**
**Next:** the first thing to do next session
**On schedule?** yes / behind by N days (and why)
```

---

## 2026-11-03 (Day 1) | Phase 0 | ~3 hours
**Goal:** Stand up the repo skeleton with one working task end to end.

**Done:**
- Project layout, pyproject, CI workflow, README, PLAN, this journal.
- First task `business_hours` (call-centre open/closed + minutes until open):
  spec, reference implementation, hidden tests.
- AST-based bug injector with 5 operators: compare swap, arithmetic swap,
  and/or swap, drop `not`, integer off-by-one.
- Mutant validation: a mutant is kept only if the hidden tests detect it.
- Grader: candidate tests must pass on the reference, then score = fraction
  of mutants they detect. `assert False` style tests score 0.
- 9 self-tests for the environment, all passing.

**Findings:**
- First run: 35 mutants, 30 kept, 5 rejected. Hand review of the 5 rejected
  showed only 3 were truly equivalent (loop bound 14 -> 13/15, a `<` vs `<=`
  at a boundary already handled earlier). The other 2 were real bugs my own
  hidden tests missed: Friday treated as non-business day when searching for
  the next opening, and the weekend skip stepping 2 days at a time.
  Added two tests; now 32 kept, 3 rejected (all equivalent).
- Takeaway for the report: the mutation filter doubles as an audit of the
  task author's tests. Rejected mutants must be reviewed by hand, never
  silently dropped. Worth tracking "hidden-test gaps found" per task.

**Blockers / risks:**
- Docker not installed on this machine. Phase 0 sandbox is a plain subprocess
  with a timeout; candidate code is not isolated yet. Must be fixed before
  running untrusted model output at scale (Phase 2).
- Speed: one pytest subprocess per mutant, ~60 s for the self-test suite.
  Fine for now; cache validated mutants to disk in Phase 1.

**Next:** Create public GitHub repo and confirm CI is green. Then write
tasks 2 and 3.

**On schedule?** Yes.
