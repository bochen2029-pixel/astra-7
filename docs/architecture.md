# ASTRA-7: Technical Architecture

Architectural decisions and their rationale. Provisional choices are marked. Update as decisions stabilize.

---

## System Diagram (Conceptual)

```
[Player at PC]
    |
    v
[UE 5.x Game Process]   <----- ship-API HTTP -----+
    |                                              |
    | HTTP / WebSocket / SSE over localhost       |
    v                                              |
[Harness Service (Python)]  -----  tool dispatch -+
    |
    | HTTP + SSE
    v
[llama.cpp Server]
    |
    v
[Qwen 3.5 9B  OR  Qwen 3.6 27B] + ASTRA-7 LoRA + canonical sysprompt
```

Three processes, all localhost:

1. **UE 5.x Game Process** (C++/Blueprint): renders the ship, runs the simulation, exposes ship-subsystem APIs over a small HTTP server inside the game.
2. **Harness Service** (Python): memory consolidation, tool routing, time abstraction, vision feed routing, audio I/O bridging, request/response logging.
3. **llama.cpp Server**: model inference, token streaming, vision input processing.

## Engine

**Unreal Engine 5 (latest stable as of 2026-05-12).** Decision: the latest 5.x release available at project start; no commitment to a specific point release yet.

## Bridge Protocol

**Provisional choice: HTTP + Server-Sent Events (SSE) over localhost, with WebSocket as an enhancement layer for bidirectional events.**

Rationale:

- llama.cpp ships an OpenAI-compatible HTTP server with native SSE token streaming. No bespoke wire protocol is required between the harness and the inference layer.
- UE 5 has first-party HTTP support (`FHttpModule`) and WebSocket support (`FWebSocketsModule`). Both fit a localhost streaming pattern without external dependencies.
- JSON over HTTP is debuggable with curl, browser dev tools, and standard logging. gRPC would require codegen, .proto schema maintenance, and a UE-side gRPC client which is not first-party.
- Tool calls fit naturally: the AI emits structured JSON in completions, the harness parses and dispatches to ship-API endpoints exposed by the UE game process.

Flow:

- **UE → Harness**: REST (POST `/conversation`, `/event`) for one-shot requests. WebSocket for streaming dialogue and AI-initiated events.
- **Harness → llama.cpp**: HTTP with SSE for token streaming.
- **Harness → UE**: HTTP callbacks to ship-API endpoints for tool calls (lights, doors, sensors, etc.).

When to revisit:

- If localhost HTTP latency becomes a measurable issue, consider Windows named pipes or memory-mapped files for the hottest paths.
- If structured tool calls become onerous over JSON, add a gRPC layer for tool calls only and keep streaming on SSE.

## Base Models

Two variants targeted, single LoRA codebase, different base weights:

- **Qwen 3.5 9B (vision-capable)** (provisional): fits comfortably on RTX 4090, faster inference, slightly lower fidelity persona. Default for minimum-spec hardware.
- **Qwen 3.6 27B (vision-capable)** (provisional): full multimodal at higher fidelity, recommended on RTX 5090.

The harness is base-model-agnostic. Swap by changing one config field plus the matching LoRA.

Quantization at inference: Q5_K_M on RTX 5090, Q4_K_M on RTX 4090 (per CLAUDE.md hardware targets).

## LoRA Hyperparameters

**Provisional configuration for the periphery LoRA.** Trained per base model. Two variants planned: one for Qwen 3.5 9B, one for Qwen 3.6 27B. Identical training corpus, separate weights.

| Parameter | Value | Notes |
| --- | --- | --- |
| Rank (r) | 16 | Top of CLAUDE.md range. Room for voice rules plus ship-API fluency. |
| Alpha | 32 | 2x rank, standard. |
| Dropout | 0.05 | Light. |
| Learning rate | 2e-5 | Matches CLAUDE.md. |
| Epochs | 3 | Top of CLAUDE.md range. |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` | Attention plus FFN projections. |
| Batch size | 1 | Gradient accumulation = 16. |
| Optimizer | AdamW | Standard. |
| Weight decay | 0.01 | Standard. |
| LR scheduler | cosine | 5% warmup. |
| Precision | bf16 | Or fp16 if hardware lacks bf16. |

Training corpus composition (provisional):

- ~60% synthetic ship-operation scenarios (canon ship-API calls, status responses, maintenance dialogues, telemetry interpretation).
- ~30% voice consistency examples (em-dash absence, anti-performance discipline, service-phrase suppression, brevity defaults).
- ~10% edge cases (refusal, disagreement, silence-as-response, frame-integrity under adversarial prompts).

Loss target: not knowledge updates. Surface-rule enforcement and ship-API fluency. Empirical tuning expected; these are starting points.

## Memory and Time

The harness mediates memory across sessions:

- **Within-session**: full conversation buffer.
- **Across cryosleep cycles**: consolidated journal entries the AI authored, weighted by salience.
- **Across game launches**: persisted save file containing harness state and fictional time elapsed.

The AI receives no wall-clock signals. Her sense of duration is computed from in-fiction events the harness has logged. No system datetime, no file timestamps, no time deltas computed against absolute time leak into her input.

## Camera-Free Zones

Engineered, not faked. The harness routes only zones with active camera devices into the AI's vision input. Private quarters and certain maintenance crawl spaces have no camera devices in the ship layout, and the harness has no code path that could fabricate a feed for them. The constraint is structural.

## Distribution

- **Game binary**: Steam, free.
- **Source**: GitHub, MIT.
- **AI bundle (sysprompt + harness configs + LoRA weights)**: Hugging Face. Bundle artifacts Apache 2.0; base model licenses apply to derived weights.

## Open Items

- Final selection of which exact Qwen 3.5 9B and Qwen 3.6 27B variants to base on.
- UE5 plugin name and structure.
- Audio bridge backend: provisional UE 5 audio module; reconsider if latency or codec support becomes a problem.
- Save file schema.
- Sysprompt mirror at `/ai/bundle/sysprompt.md`: provisional plan is a build-step copy from `/docs/astra-sysprompt.md`, single source of truth lives in docs.

---

*Provisional decisions in this document do not bind future revision. Update CLAUDE.md only after operator approval.*
