# Steam AI-Content Disclosure — DRAFT

**Status:** DRAFT, prepared 2026-06-11, well ahead of any Steam page. Written
while the guardrail architecture is fresh, per the Agentic Dev Reference §8
action item.
**[RE-VERIFY] before submission:** this draft is written against the
secondhand characterization of Valve's January 2026 disclosure rewrite
(two tiers: pre-generated / live-generated; live-generated requires a
guardrail description; in-overlay player report button on Valve's side).
Confirm the live Steamworks policy text verbatim at page-creation time and
adjust field names/structure to whatever the form actually asks.

---

## Tier 2 — Live-generated AI content (the disclosure that matters)

**Proposed form text:**

> ASTRA-7's central character — the ship's AI — is a live, locally-run
> language model (currently a Qwen-family ~27B model with a project LoRA;
> a ~9B model and a small validation model run alongside it). All
> inference happens on the player's own GPU. The game makes zero network
> calls after installation: no cloud AI, no telemetry, no transmission of
> player conversations anywhere, ever.
>
> Guardrails on the live model:
> 1. **Bounded action surface.** The AI cannot execute arbitrary actions.
>    It can only invoke a small, fixed list of ship-control functions
>    (power, navigation, sensors, logs), and every invocation is
>    validated against a typed schema by a separate deterministic layer
>    before it takes effect. Invalid or invented commands are rejected.
> 2. **Safety-critical systems are hard-locked.** Life support cannot be
>    disabled by the AI; this is enforced in the game's code, outside the
>    model entirely.
> 3. **Output filtering.** All AI text passes through automated gates
>    before the player sees it: canonical pattern filters strip
>    out-of-fiction content, and a numeric-grounding validator rejects
>    any quantitative claim not traceable to the game's deterministic
>    physics simulation (the AI never invents numbers).
> 4. **No real-world data access.** The model receives only simulated
>    ship/universe state and the player's own input. It has no clock, no
>    internet, no file access, and no information about the player beyond
>    what they type or say in-game.
> 5. **Character frame.** The AI is instructed and tuned to remain a
>    fictional ship's computer. It will refuse requests to produce
>    harmful real-world content, consistent with the base model's safety
>    training, which the project does not weaken.
>
> Players can report any concerning AI output via Steam's standard
> in-overlay reporting, and the project (open source, MIT) accepts issue
> reports on its public repository.

## Tier 1 — Pre-generated AI content

**Current truth (update before submission):** the game's shipped hand-authored
content (ship design, writing, canon, code) is human-authored with
AI-assisted engineering (which Valve's policy explicitly does not require
disclosing — dev-tool efficiency is out of scope per the Jan 2026 text).
If any AI-generated *assets* (textures, props, audio samples) end up in the
shipped build, enumerate them here at that time. As of this draft: none
ship; the audio is synthesized procedurally from simulation state (not
generated media), and no AI-generated art assets exist in the build.

## Notes for the eventual submitter

- The honest one-line summary if a short field is required: *"Contains a
  locally-run AI language model as the central character; fully offline;
  bounded tool surface with deterministic validation; output gates; safety
  systems hard-locked outside the model."*
- Keep this document updated as the guardrail architecture evolves
  (validator scope, gate lists). The disclosure should describe what ships,
  not what is planned.
- Precedent exists for shipping/auto-downloading local model weights on
  Steam with a disclosure of this shape (per the Agentic Dev Reference §1,
  evidence class (a) — re-verify the cited precedent title at submission).
