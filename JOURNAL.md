# Research Journal

Daily log for bug-bash. One entry per working session, newest at the top.
Targets and phases are in [PLAN.md](PLAN.md).

Entry template:

```
## YYYY-MM-DD (Day N) | Phase X | ~H hours
**Goal:** what this session set out to do
**Done:** what actually got done
**Findings:** anything surprising, measured, or worth putting in the report
**Caught in review:** AI-written code or tests rejected or corrected, and why
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

**Rename:** Project renamed from `defect-hunt` to `bug-bash` before the first
push. A bug bash is the QA team contest I ran and took part in for years:
everyone tries to break the product, the person with the most real bugs wins.
Same structure here with models, and the same old rules carry over: only
reproducible, correct reports count, and "most bugs" scoring invites gaming
(the human version of reward hacking), so precision gets tracked alongside
bugs found. Injected bugs now use the project prefix: `BB-<task>-NNN`.

**Published:** https://github.com/davidyoung8196504567-sudo/bug-bash (public).
CI green on Python 3.12 and 3.14. **Phase 0 complete, 2 days ahead of plan.**

**Design decisions (evening):**
- Domain: IVR first. Most recent work, and the defect types repeat on every
  project, so they make realistic bug-injection rules.
- Structure: a generic IVR simulator runs data files (call flow, prompts,
  config). Bugs are injected into the build files, not the engine, because in
  real IVR projects defects come from translating documents into
  configuration. The simulator is the system under test; walkers (my
  path-walking test generator as the non-AI baseline, and language models)
  are the test clients.
- Tests are scripted calls (data), so the grader never runs walker code.
- Everything fictional and written for this project ("Northwind Benefits
  Line"). No client material.
- I build the simulator myself; Claude pairs on injector, grader, renderer.

**Next:** Phase 1 step 1: write the IVR bug catalogue and settle the data
file formats. Cache validated mutants to disk.

**On schedule?** Yes.
