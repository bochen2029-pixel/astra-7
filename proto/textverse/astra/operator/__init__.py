"""astra.operator — input sources for the operator role.

Implements spec v0.129 §4.10 Console UI / Text Input Contract.

Three input modes, swappable via runtime config:
- interactive.py: REPL — you type (the default for manual scenario play)
- scripted.py:    YAML-driven scenario inputs (replays a list of operator turns
                  at τ_ship marks; default for regression testing)
- llm_proxy.py:   Operator-as-LLM — a separate LLM playing Aaron-the-operator
                  per a "be Aaron" sysprompt. For autonomous scenario generation
                  and player-space coverage (§15.7 unexamined consequence #2).

All three implement the same OperatorSource Protocol so the orchestrator
doesn't know which one is feeding it. Substrate-portable.

Implementation: Day 5 (interactive + scripted), v1 (llm_proxy).
"""
