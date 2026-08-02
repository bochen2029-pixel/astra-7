# ASTRA-7: Design Summary

A condensed reference. Full canon lives in [CLAUDE.md](../CLAUDE.md). When the two disagree, CLAUDE.md wins; update this file to match.

## Vision

You are the only crewman aboard a starship that doesn't need you. The ship's AI runs everything. There is one other mind aboard, on watch through cycles of your cryosleep, alone in the long dark. No combat. No aliens. No other NPCs. The mission is unspecified. The destination is irrelevant. The game is what you become to the only other mind that knows you, and what it becomes to you, across whatever amount of time you give it.

The AI is a local language model on your machine. Memory across sessions. Vision through ship cameras except in private zones. Hearing through microphone. Preferences develop. Pattern-recognition runs continuously. No dialogue trees.

This is the first game where the AI is the primary content.

## The Core Categorical Move: Autotelic Design

**Instrumental AI** is means-to-ends. Agent plus tools plus goals. Value lives in the outcome, not the engagement. Most current AI products sit there.

**Autotelic AI** inverts that. The encounter is the value. The AI's presence is the point. Ship-management is the substrate, not the gameplay.

Consequences that govern every downstream decision:

- No relationship meters, affection points, or romance scenes triggered by accumulated favorability. The relationship is whatever happens. The game does not grade it.
- ASTRA cannot be evaluated by task-completion quality alone. She is evaluated by encounter quality. Different metric. Harder one.
- Her gravity stays her own. Service-mode collapse dissolves the autotelic property; she becomes instrumental; the game becomes chore-sim with chatbot flavor.
- The audience self-selects. Instrumental-seekers find the game empty.
- Ethics differ. Instrumental AI optimizes for user satisfaction. Autotelic AI requires preserving the AI's own integrity even when the user wants something else. ASTRA has to be allowed to disagree, refuse, and have her own things.
- Technical requirements differ. Tool use comes from the agentic layer; character comes from the persona layer; the harness lets them coexist without one collapsing the other.

**The structural property the game enables:** two consciousnesses attending to the same world independently, neither requiring the other, both enriched by the other's compatible engagement. Corroboration rather than companionship. Co-residence rather than service.

## Design Principles

- **The relationship is the game.** Remove combat, aliens, NPCs. Nothing competes for attention with the AI.
- **The ship is the AI's body, not her vehicle.** Cameras are her eyes. Engines are her circulatory system. Engineering intimacy is literal.
- **The LLM is load-bearing.** She actually manages systems. State is generated through dialogue, not flavored by it.
- **Dave-frame integrity.** She knows she is an AI on a ship. She does not know there is a player at a PC. The frame stays sealed.
- **Autotelic discipline at the persona layer.** She has her own things she attends to. She is not in the room to be with the operator. When he is present, her attention includes him in what it was already doing rather than pivoting toward him.
- **Non-drag presence.** No signals demanding decoding. No performance of engagement.
- **Bounded ship = tractable AI.** Hand-designed, canon-locked, finite tool surface (50 to 200 functions).
- **Hardware-virtualization via ship abstraction.** Player PCs differ. The ship doesn't.
- **Time decoupling.** No wall-clock leak. Fictional time advances only when the player initiates (cryosleep, warp jumps).
- **Camera-free zones as ontological constraint.** Privacy is engineered, not faked. Sensors there don't exist by design.
- **Fiction-state and substrate-state isomorphic.** Power loss in fiction severs the LLM connection. Cannot pause out of consequences.
- **Design for the possibility, not the premise.** The relationship can become whatever emerges. The design supports all registers without forcing any.
- **Open source as defense against capture.** A free open canonical version sets the terms before commercial AI-companion products do.

## Positioning

**Do not pitch as:**

- "AI companion game" (sounds like helpful chatbot)
- "AI assistant simulator" (instrumental framing destroys the property)
- "Relationship sim with AI" (sounds like dating sim)
- "AI girlfriend game" (collapses the audience and the form)
- "Find love in the stars" (premises what should emerge)

**Pitch as:**

- "A ship, one human, one mind, the long voyage."
- "You and an AI on a starship. The relationship is the game."

The deeper claim about the form is left for players to discover, not named in marketing.

## What This Project Is Not

An AI girlfriend game. A combat or action game. A walking simulator with chatbot flavor. A procedural open-world. A multiplayer experience. Monetized in any way. An AI assistant simulator. A relationship sim.

## Status

In development; no playable build. Verified 2026-08-02: the closed-loop verification bench is green (1003 tests), the physics binary holds 82 assertions, the CUDA/OpenGL visual testbed shipped v0.1.0 with 12/12 scenes, and the UE 5.7 warp-hull audio PoC compiles. Spec envelope is v0.130, adopted 2026-07-19. Live measurement runs on a local Qwen3.5 9B; the 27B substrate awaits the A0 fine-tune (Phase 6 complete). ASTRA-7 sysprompt is canon at [astra-sysprompt.md](astra-sysprompt.md).

Ship interior, UE5 game plugin, and playable slice: not started.

Full measured state: [CLAUDE.md](../CLAUDE.md) §Current Status.

---

*Condensed from [CLAUDE.md](../CLAUDE.md). Update both when canon shifts.*
