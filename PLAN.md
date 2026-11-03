# Plan and Timeline

Target: apply to the Anthropic Fellows Program (January 2027 cohort) with
Phase 3 results in hand, about 2026-11-30. Phases 4 and 5 continue after the
application is submitted. Progress is logged daily in [JOURNAL.md](JOURNAL.md).

| Phase | Dates (2026) | Deliverable | Done when |
|---|---|---|---|
| 0. Scaffolding | Nov 3 - Nov 5 | Repo, CI, one task end to end | CI green on GitHub, `business_hours` graded |
| 1. Task set | Nov 6 - Nov 15 | 20-30 tasks with validated mutants | Every task: reference passes, rejected mutants reviewed by hand |
| 2. Grader + sandbox | Nov 16 - Nov 22 | Docker sandbox, scoring, attempt logs | Untrusted code runs with no network, time and memory limits |
| 3. Baselines | Nov 23 - Nov 29 | Claude API + small open model results | Results table, failure analysis, reward-hacking log |
| **Apply** | **Nov 30** | Application submitted with repo link | |
| 4. Training (stretch) | Dec 1 - Dec 14 | LoRA rejection-sampling fine-tune of open model | Before/after scores on held-out tasks, honest either way |
| 5. Write-up | Dec 15 - Dec 21 | REPORT.md | Motivation, method, results, limitations, next steps |

## Phase 1 task ideas

Domains drawn from 30 years of verification work, all written from scratch
(no client or government material):

- business_hours (done): call-centre open/closed rules
- call_flow: IVR menu state machine with retries, timeouts, language choice
- rate_limiter: token bucket with injected clock
- msg_parser: fixed-width binary message decode with checksum
- config_validator: firewall/load-balancer rule validation
- retry_backoff: exponential backoff with jitter bounds and max attempts
- semver_compare: version ordering incl. pre-release tags
- interval_merge: merging maintenance windows
- bilingual_prompt: EN/FR prompt selection with fallbacks
- ...

## Open questions

- How much spec ambiguity is acceptable? A mutant that the spec does not
  clearly forbid is unfair to the model. Review each kept mutant against the
  spec text, not just the hidden tests.
- Score per mutant vs per task: report both.
- Should the model also name the bug (line + description), scored separately
  from the test? Phase 3 decision.
