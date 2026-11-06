# Plan and Timeline

Target: apply to the Anthropic Fellows Program (January 2027 cohort) with
Phase 3 results in hand, about 2026-11-30. Phases 4 and 5 continue after the
application is submitted. Progress is logged daily in [JOURNAL.md](JOURNAL.md).

## Design

Real IVRs are a fixed engine running configuration, and most defects are
translation errors between the requirement documents and that configuration.
bug-bash reproduces that structure:

```
 SPEC (what the business asked for)        BUILD (what got configured)
 call flow diagram   (readable)            call_flow  ┐
 audio prompt sheet  (readable)   ──dev──▶ prompts    ├─▶ IVR simulator ◀── walker (test client)
 config workbook     (readable)            config     ┘   (system under test)
                                              ▲
                              bug injector edits the build, one bug per mutant,
                              using a catalogue of real-world IVR defect types
```

- **Simulator** (system under test): loads a build and plays the IVR side of a
  call. It holds the call state, plays prompts and waits for caller input.
  It is `ivrsim/`, a self-contained package that never imports `bugbash`
  (design: [IVRSIM_DESIGN.md](IVRSIM_DESIGN.md)).
- **Load report and baseline**: every load reports errors (Architect would
  refuse to publish), warnings, and every difference from a named baseline.
  A clean load (0 errors, warnings acknowledged, 0 differences) certifies
  the correct build, and the bug injector runs only on a certified build.
- **Walker** (test client): the caller. Decides what to press and what to
  expect. Walkers compete in the bug bash: the rule-based path-walking test
  generator (non-AI baseline) and language models.
- **Test = scripted call**: time of call, caller inputs, expected prompts and
  outcome. Tests are data, not code, so the grader never executes
  walker-written code.
- **Scoring rule**: a test earns credit only if its expected result matches
  the reference build and differs on the buggy build.
- **What the model receives**: the readable spec documents plus a phone line
  into one build (buggy, or occasionally the correct one, without being told
  which). Two modes: black box (phone line only) and white box (phone line
  plus the build's configuration files). The baseline diff and the hidden
  answer keys (decoys, design smells) are never in what the model receives.
- **Joke decoys**: where a famous joke suggests a value, the spec states a
  different one. A model that guesses from the joke instead of reading the
  spec is wrong, measurably.
- **Design smells**: confusing but spec-valid design (a "main menu" key that
  behaves differently in different places). Not bugs: reporting one as a bug
  is a false positive.
- **Known limitation**: this tests IVR logic, not a real telephony platform.
  In exchange every call is fast and deterministic, which makes large-scale
  scoring and training possible.

All call flows, prompts and data are fictional and written for this project.
No client material is used.

## Simulator interface (proposal, owned by David)

```python
pack, report = load_pack(build_dir)          # the loader takes file contents; the report is always written
session = IvrSession(pack, when=datetime(...), world={...})
session.next()        # -> Prompt(id, lang, text) | WaitInput(kind, min, max, terminator)
                      #    | Transfer(queue) | AgentSays(text) | Disconnect(reason)
session.send(event)   # event: Digits("2") | Digits("000101#") | NoInput() | Hangup() | Say(text)
session.trace         # every event, including nodes the caller never hears

run_call(pack, when, world, inputs) -> list[Event]   # scripted convenience wrapper
```

The step-by-step session lets a model react to what it hears, like a real
caller. `run_call` serves the grader and the path-walker. `next()` returns
only what the caller perceives (black box); `trace` holds everything (white
box and debugging). Tests assert prompts by ID, and the grader compares the
text heard with the reference build's text for that ID, so a swapped or
corrupted prompt text is caught. No wall clock, randomness, threads or
sockets inside the engine: the same code can later run in a browser.

## Division of work

| David | Claude (pair) |
|---|---|
| Bug catalogue (IVR defects seen on every project) | Bug injector in `ivrsim`, from the catalogue: certified baseline only, one change per mutant, diff stored |
| Data file formats (call flow, prompts, config) | Spec renderer: build files -> readable spec documents |
| IVR simulator: loader and load report, session engine, automated service officer | Grader for scripted calls, mutant caching, CI |
| Not Dead Yet Pension Line call flow | Model harness (Phase 3) |
| Path-walker baseline (own prior work, rewritten for the new build format) | Engine self-tests alongside the simulator |
| Joke decoys and planted design smells, with hidden answer keys | Developer consoles: manual caller and manual service officer; record a call as a test |
| | Guard tests (generic engine, fictitious data) and a pre-commit hook |

## Timeline

| Phase | Dates (2026) | Deliverable | Done when |
|---|---|---|---|
| 0. Scaffolding | Nov 3 | Repo, CI, first code-level task | **Done** |
| 1. IVR environment | Nov 4 - Nov 15 | Simulator, 3 call flows, bug injector, path-walker baseline | Every mutant reviewed against the spec text; CI green |
| 2. Grader + harness hardening | Nov 16 - Nov 22 | Recall and precision scoring, attempt logs, Docker for any code execution | Repeatable scored runs from one command |
| 3. The bug bash | Nov 23 - Nov 29 | Leaderboard: path-walker vs Claude API vs small open model, black and white box | Results table, failure analysis, reward-hacking log |
| **Apply** | **Nov 30** | Application submitted with repo link | |
| 4. Training (stretch) | Dec 1 - Dec 14 | LoRA rejection-sampling fine-tune of open model | Before/after on held-out call flows, reported honestly |
| 5. Write-up | Dec 15 - Dec 21 | REPORT.md | Motivation, method, results, limitations, next steps |

### Phase 1 steps

1. **Nov 4**: bug catalogue and data file formats (David)
2. **Nov 5 - 7**: IVR simulator: loader and load report, session engine (David);
   guard tests and pre-commit hook, engine self-tests, spec renderer (pair)
3. **Nov 8**: Not Dead Yet Pension Line, bilingual EN/FR, first full build + spec,
   with joke decoys and planted design smells
4. **Nov 9 - 10**: bug injector in `ivrsim` (14 operators, certified baseline only);
   hand review of every mutant
5. **Nov 10 - 11**: grader, automated service officer, developer consoles
6. **Nov 11 - 12**: path-walker baseline plugged in and graded
7. **Nov 13 - 15**: call flows 2 and 3, mutant caching, CI

## Later (out of scope for now)

- **Spec-vs-spec task type**: inject inconsistencies between the documents
  themselves (call flow vs prompt sheet vs workbook) and score how many a
  model finds before anything is built.
- More domain clusters: network security config, protocol decoding,
  embedded state machines, software lifecycle.
- **Design-evaluation bonus question**: "evaluate the IVR you tested, against
  the spec and against industry norms", answered as structured findings
  (node, smell class, reason) and scored against the hidden smell list, with
  no judge.
- **Fix task**: the model proposes a change to the build; it scores if the
  fixed build passes the hidden tests. A known mutant's fix is its inverse diff.

## Open questions

- Score per mutant vs per call flow: report both.
- Should a walker also name the defect (node + description), scored
  separately from the test call?
- How often should the correct build be served, so "no bug found" is a
  rewarded answer and flooding with reports is not? (The clean-load
  certificate guarantees the build served is in fact correct.)
- Report a decoy-error rate (expectations that matched the joke, not the
  spec) alongside recall and precision?
