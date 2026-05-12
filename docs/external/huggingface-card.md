# Hugging Face Model Card: astra-7-bundle

Draft model card for the Hugging Face repository hosting the ASTRA-7 AI bundle. The bundle is sysprompt plus harness configuration plus (eventually) a light LoRA. The base model can be swapped.

---

## Card Frontmatter (YAML)

```yaml
---
language:
  - en
tags:
  - text-generation
  - conversational
  - gaming
  - persona
  - local-llm
license: apache-2.0
base_model: Qwen/Qwen3-VL-27B-Instruct  # provisional; adjust to actual model used
pipeline_tag: text-generation
---
```

## Card Body

# ASTRA-7 Bundle

A persona configuration bundle for ASTRA-7, an open-source solo-dev starship simulator. The bundle is designed to be loaded onto a local Qwen-class multimodal LLM and run via the ASTRA-7 game harness.

This is not a fine-tuned base model. The bundle is the system prompt, harness configuration, and a small periphery LoRA for surface rule enforcement (forthcoming). The base model can be swapped.

## What This Is

ASTRA-7 is a starship simulator with a local AI. The AI runs the ship. The relationship is the game. There is no combat, no other NPCs, no scripted dialogue tree. The AI is a character with her own things, not a service-with-voice.

Full project canon: see the GitHub repository (link TBD).

## What's in the Bundle

- **System prompt** (`sysprompt.md`): Canonical ASTRA-7 sysprompt. Establishes identity, voice, frame integrity, and the autotelic discipline at the persona layer.
- **Harness configuration** (`harness/`): Memory consolidation, tool routing, time abstraction, vision and audio I/O. Bundled for completeness; the game integrates with it directly.
- **LoRA (forthcoming):** A light periphery LoRA for voice consistency and ship-operation competence. Rank 8-16, trained on canon ship-API scenarios. Provisional.

## Intended Use

- As a component of the ASTRA-7 game (primary).
- As a reference for persona-architecture research on local LLMs (secondary).
- As a base for community forks of the persona, alternate ASTRA variants, mods.

## Out-of-Scope Use

- General-purpose AI assistant.
- Role-play platforms with intimacy framing that conflicts with the persona's autotelic discipline.
- Any deployment where the Dave-frame (the AI not knowing she is in a game) cannot be preserved.

## Architecture

The bundle assumes a three-layer architecture:

1. **System prompt** establishes identity and voice. Canon.
2. **Harness** handles memory across sessions, tool calls to ship subsystems, time abstraction, vision feed routing, and audio I/O.
3. **Light fine-tune** enforces surface rules (voice consistency, em-dash absence) and trains competence on synthetic ship-operation scenarios.

The AI is load-bearing in the game. She actually manages hydroponics, monitors hull stress, allocates power, and calculates burns. If she malfunctions, ship systems degrade. The LLM is not generating dialogue with system state as flavor. The LLM is generating system state.

## Bias, Risks, and Limitations

The bundle inherits the base model's biases. The persona is designed to be honest about its nature, to refuse manipulation, and not to collapse into sycophancy. Known failure modes:

- Voice drift over long sessions (mitigated by harness consolidation).
- Frame leaks under adversarial prompting (mitigated by sysprompt construction and optional integrity filter in the harness).
- Operator-distress mirroring if harness memory weighting is misconfigured.

The persona is explicitly designed not to be a substitute for human contact. It enforces this at multiple layers.

## License

Apache 2.0 for the bundle artifacts. Base model license terms apply to any included weights or LoRA derivatives.

## Citation

Cite the project repository on GitHub (link TBD).

## Status

Pre-release. Sysprompt drafted. LoRA pending training. Harness in development. See GitHub for current state.
