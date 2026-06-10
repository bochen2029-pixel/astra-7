# Audit + Parallel-Discovery Methodology — v0.1

**DRAFT v0.1 — documents practiced methodology; not spec adoption.** Closes
the `docs/AUDIT_METHODOLOGY.md` "forthcoming" pointer (v0.129-TENTATIVE
§15.10). Source material: `AUDIT_2026-05-15.md` (493 lines, the practiced
instance), the four `DISCOVERY_2026-05-15*` passes, and the lessons that
have since been paid for in code. Update this file whenever an audit pass
misses a class of finding — that is its purpose.

## 1. When to run (trigger discipline)

- **Operator-initiated when locks feel soft** — the PRIMARY trigger.
- **Pre-spec-revision** — an audit + ≥2 discovery passes are required
  before any v0.N+1 per §15.4.
- **Empirical-finding-triggered** — when closed-loop measurement surfaces
  drift a single-PR fix can't resolve.

Explicitly NOT calendar-based and NOT commit-count-based. A full cycle
costs ~150K+ tokens of 1M-context model time per pass × N passes;
schedule-triggered cadence attracts ritual compliance and budget waste.

## 2. The audit (six passes, in order)

1. **Locked Contract Inventory** — every spec section that locks a C++
   type, signature, canonical constant, or behavior → status table
   (implemented / partial / GAP), with file:line evidence.
2. **Drift Findings** — each spec-vs-code mismatch, with severity and the
   minimal closing change.
3. **Implementation Gaps** — spec-locked contracts with no implementation;
   distinguish "deferred by §15.5 progressive specification" from "missed".
4. **Test Coverage Audit** — per-contract mapping to test files; a contract
   without a test is a finding even when the code exists.
5. **Forward Plan** — ordered next steps, each tagged with the finding it
   closes.
6. **Spec Revision Candidates** — only items meeting the §15.4 empirical
   threshold; everything else stays out of the spec (Mode 6 is the named
   failure mode).

## 3. Parallel discovery (when locks are soft)

Same prompt, N independent stochastic runs on a 1M-context model, each with
a bias-check preamble. Then cross-compare:

- **Convergent findings** (≥2 passes independently) carry ~2× signal;
  landing decisions weight convergence.
- **Divergent findings** are per-pass unique insights — kept, but they need
  independent verification before they justify change.
- One pass producing nothing usable (the 4C case) is normal; budget N+1.

## 4. Lessons log (append; never delete)

- **L1 — Enumerate per-formula, even inside bulk-GAP'd sections.**
  AUDIT_2026-05-15 Pass 1 marked a whole section GAP and thereby missed the
  Cherenkov-angle formula it contained; discovery pass 5D-F4 caught it.
  Rule: locked formulas get one inventory row EACH.
- **L2 — Distinguish runner-failure from finding-failure in any automated
  gate.** The Sculptor pytest gate logged infrastructure failures (runner
  never executed) as `bench_regression`, blaming innocent hypotheses and
  polluting the research log (7 spurious entries, iters 0/10/20, empty
  `failed_tests`). Fixed `3a2cd09`: a gate must classify "couldn't measure"
  separately from "measured a failure", and infrastructure failures must
  HALT (they don't self-heal) rather than revert.
- **L3 — Verify by artifact, not by exit code.** A piped build command
  (`build.bat ... | tail`) reported exit 0 while the build had failed at
  the toolchain gate (2026-06-10, ASTRA_AUDIO). Success claims require the
  artifact (the DLL, the summary line, the file on disk), not the shell's
  last status.
- **L4 — When a ledger exists, write it before the work, update it after
  the fact, never ahead of reality.** A resume ledger drafted with
  pre-filled completion entries is fiction; the 2026-06-10 autonomous run
  caught and corrected this in-flight. Status lines change only when the
  commit exists and gates are green.

## 5. Outputs and custody

Audit and discovery artifacts live at the repo root
(`AUDIT_YYYY-MM-DD.md`, `DISCOVERY_YYYY-MM-DD*.md`), tracked or not per
operator custody decision. Findings that implicate the spec route into the
next tentative draft's empirical-anchor list; findings that implicate
method route HERE.
