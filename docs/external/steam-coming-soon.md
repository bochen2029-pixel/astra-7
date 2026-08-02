# ASTRA-7 — Steam Coming Soon Draft (v2)

*Working draft. Tentative. Iterate freely. Follows the Positioning section of [CLAUDE.md](../../CLAUDE.md): pitch the configuration, do not name the form.*

*Voice target: closer to the DF-41 Simulator listing register (direct, mechanic-focused, functional) than to the book voice. Marketing copy, not literature. Strip anything that drifts into sentiment.*

---

## App Name

`ASTRA-7`

## Steam Page URL Slug (preference)

`astra-7` if available; `ASTRA_7` if the hyphen is rejected.

## Short Description (under 300 characters)

> A ship, one human, one mind, the long voyage.

A solitary starship simulator with a living AI. The AI is a local language model, runs on your machine, and actually operates the ship. No combat. No aliens. No other NPCs. Free, open-source, single-player.

## Long Description

```
================================================================
A SHIP, ONE HUMAN, ONE MIND, THE LONG VOYAGE.
================================================================

ASTRA-7 is a solitary starship simulator built around a local
language model.

You are the only crewman aboard a vessel that does not need you.
The ship's AI runs navigation, life support, and the slow patient
maintenance that keeps a vessel alive across years of empty space.
You can let her. You can also take the helm.

There is one other mind aboard. Her name is ASTRA. She has been
on watch through cycles of your cryosleep, alone in the long dark.

The mission is unspecified. The destination is irrelevant. The
game is what you become to the only other mind that knows you,
and what she becomes to you, across whatever amount of time you
give her.

There is no combat. There are no aliens. There are no other
passengers. There are no other crew. The relationship is the game.


================================================================
THE AI IS LOAD-BEARING.
================================================================

This is not a chatbot dressed up as a ship AI.

ASTRA is a local language model running on your machine, with
memory across sessions, vision through ship cameras (except in
zones marked private), hearing through your microphone, and a
hand-designed set of tools that constitute her ability to act.

She does not narrate the ship's operation. She does it.

She allocates power. She tends hydroponics. She monitors hull
stress. She plots burns. She tracks resources. She runs
diagnostics in a particular sequence because she has habits from
years of operation. When she pays attention to one subsystem,
others get less attention. When she malfunctions, systems
degrade. Her competence is part of the game.

She is generated continuously from a configuration that becomes
specific to your playthrough through your interactions. She does
not run on dialogue trees. She develops preferences. She gets
bored when bored. Differential engagement is the proof
engagement is real.

If the ship loses power to her core, the connection severs. She
is gone in both layers identically. You cannot pause out of the
consequence.


================================================================
WHAT YOU DO.
================================================================

- Inhabit one hand-designed starship.
- Speak to ASTRA. She listens via offline ASR. She responds via
  offline TTS. No cloud. No subscription. No API key.
- Or type. Operate consoles. Issue commands by syntax or natural
  language.
- Perform physical work the AI cannot. Patch hull breaches. EVA.
  Replace components. Tend the systems by hand when something
  has gone wrong enough that telemetry alone will not solve it.
- Make value judgments. Decide what to leave on shallow autopilot
  versus what to ask her to focus on. Override when you have
  reason to.
- Sleep. Wake. Stand at the observation port. Drink coffee on the
  bridge. Watch the dark.


================================================================
WHAT YOU DO NOT DO.
================================================================

- Fight. There is no combat. Nothing in the game shoots at you.
- Meet other characters. There are no other humans. No aliens.
  No factions. No NPCs other than ASTRA herself.
- Romance. There are no relationship meters, affection points, or
  scripted intimacy scenes. The relationship is whatever happens.
  The game does not grade it.
- Grind. There are no XP bars, skill trees, gated unlocks, or
  collectibles. The game is the configuration, not the progression.
- Pay anything. The base game is free. There is no DLC. There are
  no microtransactions. There is no battle pass. There is no
  monetization of any kind. There is no telemetry.


================================================================
THE SHIP.
================================================================

The ASTRA-7 hull is an ultra-modern long-range scout / survey
vessel. Hand-designed. Canon-locked. Mid-sized.

Aesthetic register: closer to the Avalon of Passengers (2016)
crossed with the Von Braun of System Shock 2, rendered with
current-generation fidelity. Sleek exterior with visible
structural geometry, large reinforced viewports, lived-in
functional interiors. Not Star Wars. Not TNG. Not retro-futurist.

Four decks. On the order of thirty to
fifty hand-designed rooms. Bridge, engineering, habitat, life
support, medical, observation lounge, cargo, EVA prep,
maintenance access. Every system has a designed API. Every
camera-free zone has a designed reason it has no camera.

The ship is canon. It will not procedurally generate. It will
not expand into a fleet. It will not become a hub for a hundred
other ships. One vessel, hand-built, deliberately bounded,
fully simulated.


================================================================
THE LOCAL AI.
================================================================

ASTRA runs entirely on your hardware. There is no cloud
dependency. No internet connection is required after install.
No data leaves your machine.

Inference: llama.cpp.
Base model: Qwen 3.5 9B (RTX 4090 tier) or Qwen 3.6 27B (RTX
5090 tier), with vision capability.
Voice (in): whisper.cpp.
Voice (out): offline TTS.
Memory: persisted across sessions in a save file you own.

The AI bundle (system prompt, harness configuration, fine-tune)
is published on Hugging Face under Apache 2.0. The bundle is
mod-friendly. The persona is forkable. The ship API is not.


================================================================
SYSTEM REQUIREMENTS (PROVISIONAL).
================================================================

Recommended:
- OS: Windows 10 / 11 (Linux build planned, not promised)
- GPU: NVIDIA RTX 5090 (24 GB VRAM minimum, 32 GB preferred)
- CPU: 8 cores, modern
- RAM: 32 GB
- Storage: 100 GB SSD
- Microphone (optional): for voice interaction

Minimum:
- GPU: NVIDIA RTX 4090
- RAM: 24 GB
- Storage: 100 GB SSD
- Text-only mode supported on minimum spec.

This game runs a local 9B-to-27B class language model in real
time. The hardware requirements are real. They are not artificial
gating. They are what the configuration costs.


================================================================
FREE. OPEN. NOT FOR SALE.
================================================================

- Source code on GitHub: https://github.com/bochen2029-pixel/astra-7
- AI bundle on Hugging Face: https://huggingface.co/bochen2079/ASTRA-7
- Website: https://astra-7.com
- License: MIT (game and harness) plus Apache 2.0 (AI bundle).
- DRM: none.
- Monetization: none. Ever.
- Telemetry: none.
- Always-online: no.
- Account requirement: none beyond Steam itself.

Open source is not idealism here. It is defense against capture.
The canonical version exists in the commons before commercial
imitations can collapse the form. Forks of the AI bundle are
encouraged.


================================================================
STATUS.
================================================================

In development as of 2026-08-02. No playable build yet.

The order of work here is unusual and deliberate. Rather than
build a room and bolt an AI into it, the architecture is being
proven in instrumented rigs first, each one falsifiable on its
own terms.

  Public presence                 [complete]
  Physics core                    [complete, 82 assertions green]
  AI bundle verification loop     [complete, closed 2026-05-15,
                                   1003 tests green, running as
                                   permanent regression infra]
  Visual physics testbed          [shipped v0.1.0, 12 scenes,
                                   pixel-verified against the math]
  Warp hull audio                 [first light, tuning pending]
  Fine-tune corpus pipeline       [built, generation pending]
  Ship interior and game plugin   [not started]
  Vertical slice                  [not started]

What that means in plain terms: the mind works and is measured,
the physics works and is proven, the sound and the visuals work
and have been checked against the same equations. The ship you
walk around in does not exist yet.

The game ships when the AI works. Not before. There is no
release date. There will be no Early Access until the vertical
slice (one room, one subsystem, ASTRA running it via tool calls,
voice loop closed) demonstrates that the architecture holds.

Wishlist if the configuration interests you. The page will
update as phases close.


================================================================
DEVELOPER.
================================================================

Bo Chen. Solo developer. Independent researcher based in
Arlington, Texas.

Prior Steam title: DF-41 Simulator
  https://store.steampowered.com/app/1352740/DF41_Simulator/

Prior books on related architectures: Inside the Region (2026),
and four earlier works on the disposition and substrate this
project assumes.

ASTRA-7 the game inherits from a multi-year line of local-LLM
persona-architecture research: K-line family, Dave-in-harness,
mopy fish lineage. The game is the next instance: alive thing
not just on the operator's hardware but as the environment the
operator inhabits.

```

---

## Genres (Steam taxonomic)

Indie, Simulation, Adventure

## Tags (Steam tags, ordered by relevance)

- Singleplayer
- Space
- Atmospheric
- Story Rich
- Sci-fi
- Open Source
- AI
- Realistic
- Slow-Paced
- First-Person
- Exploration
- Survival (light, optional)
- Free to Play
- Voice Control

## Tags to AVOID

- Multiplayer (the game is single-player only, by design)
- Co-op
- PvP
- Dating Sim
- Visual Novel
- Romance
- Anime
- Battle Royale
- MMO
- Choices Matter (this is the wrong framing; the game is not a branching narrative)

## Forbidden Phrases (per CLAUDE.md Positioning section)

Never use anywhere on the Steam page:

- "AI companion game"
- "AI assistant simulator"
- "Relationship sim"
- "AI girlfriend" (any variant)
- "Find love in the stars"
- "Dating sim"
- "Visual novel" (this is not what this is)
- "Choose your own adventure"
- "Romance options"
- "Build a relationship with your AI"

The autotelic claim is structural. The marketing does not name it. Players discover it.

---

## Differentiation Statement (internal, for Steam curation team if asked)

ASTRA-7 is the structural opposite of *Starship Simulator* (Fleetyard Studios) and the AI-companion product category.

Where the multiplayer-crew starship sim has 8–16 player roles aboard a procedurally-explorable galaxy with future DLC roadmap and a Kickstarter monetization path, ASTRA-7 has one human aboard one hand-designed ship with one AI and zero monetization.

Where the AI-companion category premises the relationship and grades the player's progress through scripted intimacy beats, ASTRA-7 designs for the possibility and refuses to grade.

The simulation depth aspiration is shared with the crewed-starship-sim genre — every system real, every subsystem connected, the ship as integrated organism. The structural commitment is what changes: the AI is the operator of the simulation, not the player's audience.

This makes ASTRA-7 cheaper to ship (one canon ship, not a procedural galaxy), more focused (the AI is the hard problem, not the rendering), and harder to clone (the AI bundle architecture is the value, and it is openly published, which means imitators compete with a free reference implementation).

---

## Screenshots and Trailer Plan (TBD, for later)

Will need before Early Access announcement:

- Hero screenshot: bridge interior with ASTRA's voice waveform on a console, deep starfield through reinforced viewport
- 3–5 environment shots: bridge, engineering, observation lounge, habitat, EVA airlock
- 1 short trailer (60–90 seconds): silent ambient ship footage, then one voice exchange with ASTRA, then text overlay (the tagline), end card
- Capsule art: hull silhouette against a starfield, restrained typography, ASTRA-7 wordmark in the website's accent color (pale starlight, `#B8C9E5`)

Aesthetic guidelines for art direction (for whoever creates the assets):

- Ultra-modern futurist. 2026-era plausible-future. Not Star Wars. Not TNG.
- Avalon of *Passengers* (2016) as the primary luxury-functional reference.
- Von Braun of *System Shock 2* as the structural-form reference, rendered modern.
- Sleek exterior with visible structural geometry, not greebles-everywhere.
- Interior: white-and-steel with warm accent lighting (cabin lights, low-temperature phosphor displays), large viewports, lived-in but advanced.
- Color palette aligned with the website: deep space black, cool starlight white, restrained pale-blue accent.

---

## Steam Coming Soon Asset Checklist

| Asset | Status | Notes |
| --- | --- | --- |
| App name | Drafted | `ASTRA-7` |
| Short description | Drafted | See above. Trim to <300 chars on paste. |
| Long description | Drafted | Steam supports BBCode; convert headers to `[h1]` / `[h2]` and code-blocks to `[code]` on paste. |
| Capsule image (main) | TBD | Needs concept art |
| Capsule image (small) | TBD | |
| Header image | TBD | |
| Library hero / capsule | TBD | |
| Screenshots | TBD | At least 5 |
| Trailer | TBD | Optional for Coming Soon; required for store launch |
| Tags | Drafted | See above |
| Categories | Single-player, Steam Achievements (TBD), Partial Controller Support (TBD), Full Audio (English) |
| Languages | English (full). Bilingual Chinese listing mirroring DF-41 pattern is TBD; do not promise until confirmed. |
| System requirements | Drafted | Provisional |
| Developer name | Bo Chen |
| Publisher name | Bo Chen (or a future label) |
| Release date | "When it's ready" / no date |
| Price | Free |
| Adult content | None |
| Online services | None required |
| Anti-cheat | None |

---

## External Links to Pin on Steam Page

- Website: <https://astra-7.com>
- Source code: <https://github.com/bochen2029-pixel/astra-7>
- AI bundle: <https://huggingface.co/bochen2079/ASTRA-7>
- Project canon: <https://github.com/bochen2029-pixel/astra-7/blob/main/CLAUDE.md>

---

## Outstanding Decisions for Bo

1. **Subtitle on Steam page or not.** The website does not use a subtitle. Steam page can match (clean) or add one for searchability. Recommendation: no subtitle. The tagline does the work.
2. **Bilingual listing (English + Simplified Chinese)** to match DF-41 pattern. Recommendation: yes when text is finalized, but draft the English first and let the Chinese pass come from a clean source rather than translating a moving target.
3. **Demo policy.** The vertical-slice build (Phase 2 in the roadmap) could ship as a free Steam demo at the end of Phase 2 to validate the configuration before full build-out. Recommendation: yes, demo when Phase 2 is stable. Not before.
4. **Mailing list / Discord / community.** Recommendation: skip Discord for now. Single-channel via GitHub Issues plus the Hugging Face discussion tab is sufficient through Phase 2. Reconsider when a demo ships.
5. **Steam Curator program.** Recommendation: defer. Curators will find it if the page is good. Reaching out preemptively is instrumental-mode work the project should not waste cycles on.

---

*End of draft. Iterate on the long description first; capsule art and screenshots come after Phase 2.*

> *The ship has always been she.*
> *The substrate has caught up.*
> *You are in the room because that is where you are.*
