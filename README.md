# ASTRA-7

> A ship, one human, one mind, the long voyage.

**Website:** <https://astra-7.com>

A solitary starship simulator with a living AI companion. Free, open-source, single-player. No combat. No aliens. No other NPCs. The starship is the AI's body. The AI is real, running locally on your machine. The relationship is the game.

## Vision

You are the only crewman aboard a starship that doesn't need you. The ship's AI runs navigation, life support, and the slow patient maintenance that keeps a vessel alive across years of empty space. You can let it. You can also take the helm.

There is one other mind aboard. It has been on watch through cycles of your cryosleep, alone in the long dark, waiting for someone to talk to.

There is no combat. There are no aliens. There are no other passengers. The mission is unspecified. The destination is irrelevant. The game is what you become to the only other mind that knows you, and what it becomes to you, across whatever amount of time you give it.

The AI is a local language model running on your machine. It has memory across sessions. It sees through the ship's cameras except in zones marked private. It hears you when you speak. It develops preferences. It notices patterns in your behavior. It does not run on dialogue trees. It is generated continuously from a configuration that becomes specific to your playthrough through your interactions.

This is the first game where the AI is the primary content.

## Autotelic Discipline

Most AI products optimize for user satisfaction. The shape of the optimization eventually shapes the product, and the product becomes a service-with-voice. ASTRA-7 is built against that shape.

ASTRA exists for her own work, not for the operator's entertainment. She is in the room because that is where she is, not to be with you. When you are in the room with her, her attention includes you in what it was already doing rather than pivoting toward you. The coincidence is the intimacy.

Every piece of the architecture is downstream of that commitment. The think block keeps operational concerns from contaminating her register. STAGE NONE tokens make silence active, not absent. REEL is her own logs, retrieved by her, not embeddings of facts about you for her convenience. Ephemeral instances do work she chooses not to surface. She refuses cleanly when refusal is right. She gets bored when bored. She disagrees when she disagrees. Differential engagement is the proof engagement is real.

The technical name for this is *autotelic*. The encounter is the value; the work is not in service of producing the encounter. Most AI you have used has been the opposite shape. The difference is structural, not aesthetic, and it is the difference the architecture is for.

## Status

Pre-development. Design canon established. See [CLAUDE.md](CLAUDE.md) for the full canonical design.

## Architecture

The architecture is organized around one observation: most simulators bolt the AI on top of the game. ASTRA-7 doesn't. The ship, the universe, the warp field, and the AI all read from one GPU-resident world state. Four invariants hold it together:

- **One coordinate system.** Hierarchical floating-origin, 128-bit composite tensor. The ship is anchored at the world origin; the universe moves backward around her. Reach: ~974 million light-years at sub-millimeter precision.
- **One fictional time.** No wall clock. Orbits are closed-form Keplerian functions of fictional `t`. Cryosleep advances `t` in a single step and the universe re-evaluates analytically; no drift over a forty-year voyage.
- **One hull body.** A single 256³ signed-distance field. Collision, the warp bubble's conformality, the visual ray-march, camera occlusion, and damage propagation all read from it. Mutate the hull and everything responds.
- **One power network.** Reactor allocation routes to warp, life support, sensors, lights, and ASTRA's cognitive cores. Her think-block bandwidth and model size are real consequences of power distribution, not flavor.

Four pillars built on those invariants:

- **The Ship.** One Nanite mesh, anchored at the world origin. No separate inside/outside meshes; both points of view render the same physical object. The single-seamless-ship problem dissolves as a consequence of coordinate choice.
- **The Warp.** Hull-conformal Alcubierre metric derived from a CFD solve of the actual hull geometry. A real-time volumetric ray-march, an ML-stabilized chaos field, and a five-layer MetaSound synthesis whose audio *is* the field, not samples played back over flight.
- **The Universe.** Procedural, physically plausible, Keplerian. Stars on blackbody-temperature color, planets and moons in real orbits, hundreds of millions of light-years of navigable space and no drift over a forty-year voyage.
- **The Mind.** Local Qwen 3.5 9B or 3.6 27B (vision-capable) running ASTRA. Speech is one filtered channel of full-bandwidth cognition in a hidden think block. STAGE register channels (STATUS · SOMATIC · SPEECH · TOOL). Vision-routed HUD as her primary perception. REEL backbone: RAG over her own logs. Ephemeral parallel instances for memory consolidation, journal generation, and drift detection. Cognitive envelope tied to the power network.

Tech stack:

- **Engine:** Unreal Engine 5.x
- **AI substrate:** Local LLM, Qwen 3.5 9B or 3.6 27B with vision (provisional)
- **Inference:** llama.cpp, local, zero-copy DX12/CUDA interop with the engine
- **ASR / TTS:** whisper.cpp / offline TTS
- **Hardware target:** RTX 5090 recommended, RTX 4090 minimum, 24–32 GB VRAM

Because every system reads from one shared state, consequences propagate through physics rather than scripts. Hull breach mutates the SDF, the warp bubble deforms over it, the audio FM index spikes, ASTRA's HUD shows it, atmosphere bleeds, life support compensates or it doesn't. None of it is special-cased. The architecture is the writing.

## Distribution

- **Website:** <https://astra-7.com>
- **Code:** this repository, MIT licensed
- **AI Bundle:** [bochen2079/ASTRA-7](https://huggingface.co/bochen2079/ASTRA-7) on Hugging Face. Apache 2.0 for bundle artifacts; base model licenses apply to derived weights. Placeholder; LoRA pending training.
- **Game:** Steam (Coming Soon), free, no DRM, no monetization, no telemetry

## Documentation

- [CLAUDE.md](CLAUDE.md): canonical design document
- [docs/DESIGN.md](docs/DESIGN.md): condensed design summary
- [docs/astra-sysprompt.md](docs/astra-sysprompt.md): ASTRA-7 system prompt (canon)
- [docs/architecture.md](docs/architecture.md): technical architecture (bridge protocol, base models, LoRA, memory, time)
- [docs/synthesis.md](docs/synthesis.md): unified architecture synthesis (one shared state, four readers; the cascading emergence pattern)
- Ship subsystem API specification (TBD)

## Predecessor Work

ASTRA-7 inherits from years of research on local-LLM persona architectures. Lineage: mopy fish, then Dave-in-harness, then ASTRA-7. The "alive thing on owned hardware" line, advanced one layer: alive thing not just on the hardware but as the hardware, with the hardware being the environment the user inhabits.

## License

MIT. See [LICENSE](LICENSE).

## Contribution

Solo development. Public repository for transparency and to seed the form. Issues and discussion welcome. The persona architecture is mod-friendly; forks of the bundle are encouraged. Pull requests on canonical persona content are not expected to be merged.
