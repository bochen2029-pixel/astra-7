"""astra.harness.ephemeral — background instances spawned during maintenance.

Implements spec v0.128 §4.9 ephemeral instance roles:
- consolidator: reviews recent conversation, scores salience, produces clean
                long-term REEL entries (calculator-bound for any numerics)
- journal_generator: §3.9 dual-clock journal output during cryosleep regimes
                     (output subject to leak detector before REEL commit)
- drift_detector: scans recent turns for register drift; emits corrections
                  via REEL entry (audit register)

Each ephemeral is an LLM bundle in its own right — calculator-bound, with
its own sysprompt. They write to the State Bus and REEL; they do NOT emit
to the operator directly (§4.9 invariant: ephemeral instances don't interact
with each other or with the operator; only the State Bus and REEL).

Implementation: deferred. v0 closes the loop without ephemerals; they land
when scenarios surface the need.
"""
