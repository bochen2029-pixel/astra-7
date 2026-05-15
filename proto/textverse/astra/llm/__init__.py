"""astra.llm — three LLM clients, calculator-bound by default.

Implements spec v0.128 §4.1 Substrate Contract, §4.9 Harness Contract, §6.4
Narrator-LLM Contract, §15.6 Calculator-bound LLM agency.

Three LLM instances on three llama-server ports:
- ASTRA-LLM (port 8080):    Qwen 27B target / 9B fallback. In-character cognition + STAGE emission.
- Narrator-LLM (port 8081): Qwen 9B. Calculator-bound. Renders physics state to perception text.
- Adapter-LLM (port 8082):  Qwen 3B or rules-based. Normalizes loose TOOL bodies to validated JSON.

Each bundle wraps its client in CalculatorBoundValidator (§15.6) — numeric tokens
in output that don't trace to a tool-call result are rejected, retried, or
flagged as drift.

Files:
- client.py:           OpenAI-compat HTTP+SSE base class
- llama_server.py:     Sidecar lifecycle (3 instances)
- astra_bundle.py:     ASTRA-LLM bundle
- narrator_bundle.py:  Narrator-LLM bundle (calculator-bound)
- adapter_bundle.py:   Adapter-LLM bundle
- validator.py:        CalculatorBoundValidator wrapper

Implementation: Day 4.
"""
