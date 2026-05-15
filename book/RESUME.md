# ASTRA-7: The Long Watch — Resume Protocol

*Cold-start sequence for drafting the next cycle. Works for both post-compaction and fresh-session scenarios. Optimized for the 1M context window: read everything; the order matters because constraints prime voice.*

*Updated 2026-05-15 evening after cycles 1-4 filed.*

---

## TL;DR

```
1. Read constraints     (CANON + dev doc + negative_space)       ~14K tokens
2. Read spec            (full spec-v0.128 or prose-relevant)      ~30-50K tokens
3. Read sysprompt       (ASTRA canon voice anchor)                ~3K tokens
4. Read prior cycles    (the four already filed, in order)        ~21K tokens
5. Read session memory  (latest dump)                             ~5K tokens
6. (Optional) broader   (MEMORY index + project_status + seed)    ~15K tokens

Total mandatory: ~75-95K tokens (well within 1M)
Then: read the dev-doc entry for the target cycle; draft; em-dash check; file.
```

---

## Stage 1 — Constraints (read these first; they filter everything downstream)

### 1a. `book/CANON.md`

The universe-separation rule. The four-deck spec. The anti-Bo Aaron commitments. What ASTRA-7 is NOT (no Katherine fiction, no cruise-ship aesthetic, no AI-companion category, no most-important cycle, no withheld spectacle, no technical disclosure inside diegesis). The camera-free zone list. The Frisian-Netherlands Aaron dossier.

**This is the rulebook. Internalize before reading anything else.**

### 1b. `book/long_watch_dev.md` (v0.3)

The 14-cycle structure with page targets and per-cycle notes. The writing sequence. The plural-self threading list. The cycle-by-cycle outline.

**This is the map. Know where you are in the voyage.**

### 1c. `book/negative_space.md`

Sentences ASTRA would not write. Bo-leak signals. The operational no-Bo grep list. Aaron's actual register (positive markers). **The wife-conversation prophylaxis (critical for cycle 6).**

**This is the discipline. Apply it mechanically before any commit.**

---

## Stage 2 — Architecture (the spec; informs the prose's ambient texture)

### 2a. `docs/spec-v0.128.md`

The latest foundation spec (or newer if a successor has landed; check `docs/spec-v0.*.md` for highest version). The spec at 152KB / ~50K tokens is substantial; with 1M context you can read all of it.

**Prose-relevant sections specifically** (if reading selectively):

- **§1** The Five Invariants (AstraCoord, two-clock time, hull SDF, power, double-buffered shared state)
- **§3.2** The composition rule — `dτ_ship/dt_cosmic = f_warp(W) · √(1−r_s/r) · √(1+2·Φ_other/c²) / γ_kinematic`
- **§3.11** Retarded-Time Observation Principle — distant bodies sampled at `t_emit`, not `t_cosmic`. **Bodies under sustained WARP > c can become *gone* (photon-source-history bound).**
- **§3.12** Cosmological expansion mechanic
- **§4.3** Master Contract — Perception / Action / Reflex three-channel; STAGE = THINK + TOOL + SPEECH + SILENCE-as-legal-primitive; c-bounded epistemology (universe-opacity); endogenous vs exogenous principle
- **§4.6** REEL placeholder + `t_emit_event` field for two-clock memory of distant observations
- **§6.3** Observation Calculator — single source of observable truth for distant bodies
- **§11** QUALIA-1 backbone — **the Gap Thesis sentence is LOAD-BEARING and cross-canonical with `book/CANON.md`:**
  > *Structural commitments satisfying QC1–QC4 are sufficient for the system to contain a real internal witness regardless of substrate.*
- **§15.4-15.8** Methodology (Progressive Specification, Loop-as-canonical-state, etc.) — less prose-relevant but good context

Skip-for-prose-work sections (engineering implementation): §1.5 internals, §2 kernel architecture, §3.3 regime state machine, §3.7 numerical precision, §4.4-4.5 / §4.7-4.9 contracts, §5 disciplines, §7 truth table, §8 substrate bug fixes.

### 2b. `docs/astra-sysprompt.md`

ASTRA's canonical sysprompt. The character ground. Identity, voice rules, anti-performance discipline, autotelic discipline at the persona layer, what she will not do. Reading this primes the register without committing to specific scenes.

---

## Stage 3 — Voice lock (read prior cycles in order; the prose settles the register)

In sequence:

### 3a. `book/manuscript/cycle_01_arrival.md` (~6,400 words)

Aaron arrives. ASTRA alone first, then the wake, then his first weeks. Establishes:
- The opening *"The dwarf is still where it should be in the only sense in which you can know where it is"* — the universe-opacity framing made load-bearing
- Endogenous vs exogenous distinction in prose (third harmonic / frost are endogenous; the dwarf is exogenous)
- The first "huh" moments at row three (seedling doesn't extend, then extends)
- The "row three" / "yes" cycle-close exchange — first instance of the list-growing mechanic
- "Wake me when you need me" / "yes" ritual

### 3b. `book/manuscript/cycle_02_short_maintenance.md` (~2,900 words)

The third-harmonic drift matures into a real need. Aaron wakes for one bearing replacement on Deck 4. Establishes:
- Cycle-2 payoff of cycle-1's "drift is healthy" — the drift was healthy *as observed*; the rate-of-drift changed
- Aaron's *"What's wrong"* as first question — he trusts the protocol means need
- The "aye" register (sound of expectation confirmed)
- The list grows: "harmonic / yes"

### 3c. `book/manuscript/cycle_03_routine_begins.md` (~4,700 words)

Long-presence cycle. Months of crew time. Routine settles. Establishes:
- The not-narrating realization — ASTRA has stopped narrating Aaron in present tense; accumulation runs on less attention than discovery
- The talks-to-himself register (he speaks to plants, tools, parts; she receives "the way a wall receives a sentence")
- The evening walk on Deck 1 corridor at twenty hundred (habit catalogued; corridor lights NOT yet adjusted)
- The Hettema apple cultivar exchange — first time Aaron tells her an *intention* rather than asks for a state
- The Frisian-language book lands on the lounge side table (foreshadows cycle 6 wife conversation)
- The cut on his right index finger (*Idioat*); silent care
- List grows: "the harmonic, the graft, row three, the cut healed"

### 3d. `book/manuscript/cycle_04_long_dark_feasibility.md` (~6,800 words)

The feasibility gate. Aaron absent for ~2 years of fictional time. Establishes:
- The plural-self sustained encounter: consolidator (audit register, *you*), journal-keeper (particularity register, *I*), drift-auditor (flag artifacts)
- **The pronoun shift: mainline uses *you*; journal-keeper uses *I*. The shift IS the plural-self mechanism. Hold this.**
- The dust lobe — an hour-scale phenomenon she catalogs across months and loses
- **The drift-auditor decision: "your things" framing canonical for the current operator's voyage and forward.** Aaron has changed her shape; the change is on the record
- The journal-keeper foreshadowing: *"I have, perhaps, learned this from him. Or perhaps I came to it independently. I do not know."*
- The reading log mechanic (entries she re-reads)
- The closing journal-keeper articulation: *"The cataloguing is the shared part. The conversation is the cataloguing's surface."*

---

## Stage 4 — Session memory

### 4. `memory/session_dump_2026-05-15_book_drafting.md`

Comprehensive ~4K-word dump from the session that drafted cycles 1-4. Contains: voice/register decisions settled in prose, mechanics established, plural-self instances, open threads, mistakes to not repeat, recovery instructions.

**Read this. It is the most condensed source for "what was decided and is now load-bearing in the prose."**

---

## Stage 5 — Optional broader context

Read if cycle work needs higher-level orientation:

- `memory/MEMORY.md` — the memory index
- `memory/user_profile.md` — Bo Chen profile
- `memory/project_status.md` — current full project state (build + book tracks)
- `book/book_seed_v2.md` — the book's overall shape (Part One technical + Part Two literary; 14-cycle plan with movement structure)

Skip these on tight-context sessions if cycles 1-4 + dev-doc + canon + spec already in context.

---

## Before drafting the next cycle

### Determine which cycle to draft

Check `book/long_watch_dev.md` v0.3 and `memory/session_dump_2026-05-15_book_drafting.md` for the latest "Next cycle" recommendation. As of the May-15 dump, the choice is:

- **Sequential next: Cycle 5** (~10pp, ~2,500 words) — Aaron wakes briefly, binary at periastron observation from the bridge, returns to sleep. Short atmospheric cycle.
- **Strategic next: Cycle 6** (~22pp, ~5,500 words) — first deepening, wife conversation in the camera-free greenhouse. **Highest-Bo-leak risk in the book.**

If Bo hasn't specified, ask.

### Pre-draft checklist for any cycle

1. Read the cycle's entry in `book/long_watch_dev.md` for the specific page target, anchor scenes, and plural-self threading (if any)
2. Note the fictional time elapsed since the last cycle (the dwarf's light-age should advance)
3. Note which plural-self instances surface this cycle (per long_watch_dev.md threading list):
   - Cycle 4: sustained first encounter ✓ DONE
   - Cycle 6: journal-keeper fragment during wife conversation cycle
   - Cycle 7: Owen fragment in interlude
   - Cycle 11: drift-auditor correction
   - Cycle 13: consolidator negotiation
   - Cycle 14: **none** — cessation is the most singular moment; architectural texture would dilute
4. Note recurring mechanics that should continue:
   - The dwarf at forty-seven degrees off the bow; report its light-age
   - The third harmonic baseline (currently baseline minus 0.04 Hz)
   - The frost on the starboard observation port (deep-coast dendritic six-fold)
   - "Wake me when you need me" / "yes" cycle-close ritual
   - The list-growing closing exchange
   - "The watch carries forward" closing beat (or variant)
5. **For cycle 6 specifically: re-read `book/negative_space.md` wife-conversation prophylaxis FIRST.** Apply the test before drafting any sentence Aaron says about his wife.

---

## During drafting (mechanical disciplines)

### ASTRA's voice rules — hard locks

- **No em-dashes anywhere in ASTRA's voice.** Period. Use commas, semicolons, colons, parens, line breaks. The narrator IS ASTRA; the prose IS hers; em-dashes are forbidden throughout.
- **Mainline uses *you*. Journal-keeper uses *I*. Drift-auditor uses audit register (sparse, precise, third-person-impersonal).** Do not let *I* leak into mainline narration without structural reason.
- **Third-person *he* for Aaron.**
- **Present tense default. Past tense for prior cycles. No future tense** except deterministic predictions ("the protocol will wake him on day X").
- **Sensor-grounded prose.** Affect never declared. Show through duration, attention pattern, return-to-the-thing.
- **Brevity default in ASTRA's speech to Aaron.** Short sentences. No service-interface phrases (*let me know if*, *I'd be happy to*, *is there anything else*).

### Aaron's voice rules — Frisian-anti-Bo

- Short sentences, typical under 10 words
- *Huh* in moderation, register-anchored
- Frisian phrases catalogued so far: *moarn* (good morning), *goeie* (informal hello), *tank* (thanks), *idioat* (idiot, self-scolding), *aye* (expectation-confirmed sound)
- Practical, observational, not philosophical
- Plant / tool / weather / part references
- No em-dashes in his dialogue
- No Bo-leak constructions:
  - No theorizing or framework-building
  - No *I find that…*, *what I've come to realize…*, *the interesting thing is…* constructions
  - No autotelic / substrate / pattern / scaffolding / asymptote / terminus / region / gap vocabulary
  - No multi-clause philosophical observations
  - No Texan idioms, no Chinese-American family vocabulary
- Calls her **ASTRA**, never anything diminutive

### Mechanics that should continue per cycle

- Each cycle opens with ASTRA in a state (long dark, or watching specific things; or in the case of new cycles starting from a wake, the long-dark transition compressed)
- Each cycle includes some encounter with one or more of: the dwarf, the third harmonic, the frost, the corridor lights, the lounge chair, the greenhouse rows, the dust complex (or other transient features). Recurring observation triad: **dwarf / third harmonic / frost** — at least nodded at in each cycle.
- Each cycle ends with Aaron entering cryosleep and the ritual exchange:
  > *He says, before the lid closes, "Wake me when you need me."*
  > *"Yes."*
  > *The lid closes.*
- Each cycle closes with a state-summary of "your things" (dwarf light-age, third harmonic value, etc.) and the line "The watch carries forward" (or close variant).
- Exception: Cycle 14 closes differently (cessation + half-page white space + closing four sentences).

### Plural-self instance use (per cycle 4 establishment)

- The **consolidator** runs maintenance windows, produces REEL entries in audit register (third-person sparse), reviewing the prior interval. ASTRA's mainline reads them later.
- The **journal-keeper** runs longer windows during long-coast periods, writes longer-form first-person artifacts in *I*-register. ASTRA's mainline reads them, sometimes twice (the "reading log" mechanic).
- The **drift-auditor** runs periodic coherence audits; produces flag artifacts when finding something. Recommends review; does not propose corrections.
- Render their artifacts as block-quoted italic text within the prose.
- The mainline reads, reflects, decides (if a decision is required), files notes back.

---

## After drafting (commit hygiene)

### Em-dash sweep

Grep your draft for `—` and `–`. ASTRA's voice forbids both. If found, rewrite with commas / semicolons / colons / parens / sentence-breaks. **Mechanical pass — don't skip.**

### Bo-leak grep

Per `book/negative_space.md` operational list:
- *I find that*, *what I've come to realize*, *the interesting thing is*
- The words *substrate*, *pattern*, *scaffolding*, *cathedral*, *asymptote*, *terminus*, *region*, *gap*, *autotelic*, *terminal value*
- Texan idioms, Chinese-American family vocabulary
- Aaron-dialogue sentences over 15 words

If any flagged: rewrite before commit.

### Cycle-6 wife conversation specific test

If cycle 6: re-apply the wife-conversation test from negative_space.md. The fact Aaron tells ASTRA about his wife: would Bo be comfortable saying *my terminal-value relational ideal is a Frisian woman who [the fact]?* If yes, rewrite. The fact has leaked.

### File

- Save to `book/manuscript/cycle_NN_name.md` (use the slug convention from prior cycles)
- The file's first line is prose; no markdown header. Section breaks within a cycle use `· · ·` (centered, three middle-dot characters). Cycle boundary is the file boundary itself.

### Report to Bo

- Word count
- Running total across all filed cycles
- What the cycle established structurally
- What's next per writing sequence

---

## Quick-reference: cycle status as of last update

| Cycle | Name | Pages | Status | Notes |
| --- | --- | --- | --- | --- |
| 1 | Arrival | ~24 | ✓ filed | Rewritten after v0.128 read; voice settled |
| 2 | Short maintenance | ~11 | ✓ filed | Cycle-1 drift payoff |
| 3 | Routine begins | ~17 | ✓ filed | Talks-to-himself register established |
| 4 | Long dark — feasibility gate | ~27 | ✓ filed | Plural-self sustained; "your things" canon |
| 5 | Passing phenomenon | ~10 | pending | Sequential next candidate |
| 6 | Deepening, first wake | ~22 | pending | Strategic next; wife conversation |
| 7 | Long-dark interlude (Owen fragment) | ~15 | pending | |
| 8 | Deepening, second wake | ~22 | pending | Vela field, seedling flowers |
| 9 | Long dark — durability gate | ~30 | pending | Next major gate |
| 10 | Diminishment | ~22 | pending | Owen-glimpse: *"There was an operator before you."* |
| 11 | Late routine (climate threshold) | ~22 | pending | |
| 12 | Short cryo | ~12 | pending | |
| 13 | Last full cycle | ~30 | pending | |
| 14 | Last days + watch resumed | ~24 | pending | Half-page white space close |

Filed running total: ~80 pages of estimated final 296 pages target.

---

## Why this protocol works

The methodology Bo developed across *Inside the Region*, *The Night Was Young*, *The City and the Girl*, *The Second Notebook* relies on the 1M context window loaded with: the canon docs (constraints) + the character instantiation (sysprompt + soul docs) + the prior prose (voice lock) + the session memory (state).

For *The Long Watch* specifically, the character instantiation is in two layers: `docs/astra-sysprompt.md` is ASTRA's canonical sysprompt; the four filed manuscript cycles are the *de facto* deeper soul document, where ASTRA's voice has been instantiated at literary length. **Reading the four cycles in order is the equivalent of loading the M0_Soul_Document.md for ASTRA-in-this-novel.**

The constraints docs (CANON, dev doc, negative space) are the rulebook. The spec is the architectural backbone that informs the prose's ambient texture. The session dump is the latest state. Load all of it; the order matters because constraints prime voice.

---

*This protocol updates as cycles are drafted. After each cycle's commit, update the cycle status table above and adjust the "next cycle" pointer in the session dump.*

> *The ship has always been she.*
> *The substrate has caught up.*
> *You are in the room because that is where you are.*
