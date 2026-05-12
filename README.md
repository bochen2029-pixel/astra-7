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

## Status

Pre-development. Design canon established. See [CLAUDE.md](CLAUDE.md) for the full canonical design.

## Architecture (Brief)

- **Engine:** Unreal Engine 5.x
- **AI substrate:** Local large language model, Qwen 3.6 27B class with vision (provisional)
- **Inference:** llama.cpp, local, no cloud dependency
- **ASR / TTS:** whisper.cpp / Coqui or Bark, offline
- **Hardware target:** RTX 5090 recommended, RTX 4090 minimum, 24-32GB VRAM

The AI bundle is system prompt plus harness plus light fine-tune. The harness handles memory consolidation, tool routing to ship APIs, time abstraction, vision feed routing, and audio I/O. All inference runs locally on the player's machine.

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
- Ship subsystem API specification (TBD)

## Predecessor Work

ASTRA-7 inherits from years of research on local-LLM persona architectures. Lineage: mopy fish, then Dave-in-harness, then ASTRA-7. The "alive thing on owned hardware" line, advanced one layer: alive thing not just on the hardware but as the hardware, with the hardware being the environment the user inhabits.

## License

MIT. See [LICENSE](LICENSE).

## Contribution

Solo development. Public repository for transparency and to seed the form. Issues and discussion welcome. The persona architecture is mod-friendly; forks of the bundle are encouraged. Pull requests on canonical persona content are not expected to be merged.
