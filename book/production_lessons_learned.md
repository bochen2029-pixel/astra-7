# Production Lessons Learned — Totality

**Compiled:** 2026-05-15 (for *The Long Watch* / ASTRA-7 book production)
**Source corpus:** All process-relevant documents at `C:\Claude-Titanic\` and its three book-project subdirectories: `the_city_and_the_girl\`, `the_night_was_young_cover_kdp_hardcover\` (artifacts only), `the_second_notebook\`. Plus root-level scripts that build all three books.
**Books shipped from corpus:** *The Night Was Young* (Titanic novella, ~53K words), *The City and the Girl* (~31K words), *The Second Notebook* (novella).
**Formats produced across the three books:** KDP paperback, KDP hardcover (case laminate), Mixam premium hardcover (case wrap, hardcover-with-dust-jacket variant), Kindle ebook, single-file digital PDF.

This is the canonical reference for Bo Chen's next book production cycle. Every concrete spec, gotcha, and tested pattern from the prior three books lives here. The companion file at `C:\Claude-Titanic\PRODUCTION_LESSONS_LEARNED.md` was the seed; this document supersedes it by reconciling with the newer code (which mutated specs after that file was frozen) and integrates lessons from the other two books that the original document didn't cover.

---

## Table of Contents

1. [Writing methodology](#1-writing-methodology) — M0 soul documents, multi-pass revision, parallel-instance audit
2. [Voice discipline](#2-voice-discipline) — Bo-voice fingerprint, anti-LLM-leak prophylaxis, lint protocols
3. [Workflow patterns](#3-workflow-patterns) — File organization, version naming, session protocols, CONTINUATION prompts
4. [Editing and revision lessons](#4-editing-and-revision-lessons) — Pass ordering, mechanical sweeps, manuscript lint script
5. [Cover design lessons](#5-cover-design-lessons) — Front, back, spine; AI art sourcing; typography baked vs. dynamic
6. [Paperback formatting lessons](#6-paperback-formatting-lessons) — Trim, margins, fonts, headers, page numbers, ToC, front matter
7. [Hardcover formatting lessons](#7-hardcover-formatting-lessons) — Case laminate vs. case wrap, KDP vs. Mixam differences
8. [KDP-specific lessons](#8-kdp-specific-lessons) — File requirements, spine math, hardcover wrap math, validator quirks
9. [Mixam-specific lessons](#9-mixam-specific-lessons) — Filename routing, panel separation, 0.80" bleed convention
10. [Kindle ebook lessons](#10-kindle-ebook-lessons) — Reflowable rules, Heading 1 ToC, content parity discipline
11. [Digital PDF distribution lessons](#11-digital-pdf-distribution-lessons) — Front matter stripping, cover crop math
12. [Platform comparison](#12-platform-comparison) — KDP vs. Mixam trade-offs
13. [Metadata and marketing](#13-metadata-and-marketing) — Listings, categories, BISAC, keywords, blurb engineering
14. [Pricing and royalties](#14-pricing-and-royalties) — What was learned about ROI
15. [Common mistakes and gotchas](#15-common-mistakes-and-gotchas) — The catalog of things that cost time
16. [Successful patterns to repeat](#16-successful-patterns-to-repeat) — Repeatable templates
17. [Cross-project contradictions](#17-cross-project-contradictions) — Where the corpus disagrees with itself
18. [Reference: tested script inventory](#18-reference-tested-script-inventory)
19. [Reference: exact-numbers cheat sheet](#19-reference-exact-numbers-cheat-sheet)

---

## 1. Writing methodology

### 1.1 M0 soul-document pattern

Both *The City and the Girl* and (less formally) *The Night Was Young* used a "Maximum-Zero" (M0) soul-document pattern at draft-zero:

> **From `the_city_and_the_girl\M0_Soul_Document.md`:** A 54K-character consciousness architecture describing the protagonist before any prose was written. Sections covered existence/ground, interior life, body, creative life, relational architecture, voice, behavioral patterns/tells, failure modes/anti-patterns, what the character is NOT, integrated self, and notes on instantiation.

> **Companion file:** `M0_System_Prompt.md` (~12K characters) — the same character compressed into a first-person system prompt that a Claude instance could "be."

**The structural test the soul document is built around:** "Two voices describe the same person. That convergence is the document's structural test. Where they diverge, the document is wrong." The document writes the character from outside and from inside; the seams between the two voices reveal weaknesses.

**Why M0 matters before draft 1:** A character whose architecture is complete before prose begins behaves consistently across scenes without an author having to retroactively patch contradictions. Every "she would never say that" moment dissolves because the document already constrains it.

**For ASTRA-7 / *The Long Watch*:** The CANON.md and negative_space.md at `C:\ASTRA-7\book\` are functional equivalents of M0. ASTRA herself has a soul document in the ASTRA-7 sysprompt at `docs/astra-sysprompt.md`. Use the same convergence test: read ASTRA from outside (the operator's view) and from inside (her own voice) — where they diverge, fix.

### 1.2 Multi-pass revision pattern

*The Night Was Young* shipped after **8 numbered passes** plus an extended Pass 6 that fragmented into 15 sub-insertions. The pass topology converged on:

| Pass | What it does | Source markdown evolution |
|---|---|---|
| 0 — Full rewrite | De novo revision from draft using full source corpus in 1M context | `part[1-5]_revised.md` |
| 1 — Phenomenology corrections | Historical/sensory accuracy sweep against research returns | `_revised_v2.md` |
| 2 — Mode B peak rewrites | Convert 8 peak emotional moments from analytical to raw perceptual prose | `_revised_v2.md` |
| 3 — UE5 walkthrough | Insert specific concrete details captured from an Unreal Engine 5 model walkthrough | (planned, optional) |
| 4 — Deep research corrections | Late-arriving research findings (e.g., tantalum vs. tungsten filaments) | `_revised_v3.md` |
| 5 — Biographical insertions | Specific character-history beats from a late-arriving source document | `_revised_v4.md` |
| 6 — Thematic integration | Cross-cutting motifs threaded across all chapters | `_revised_v5.md` and `_v6.md` |
| 7 — The single load-bearing comprehension | The novel's "Rubaiyat" — the comprehension the book exists to reach | `_revised_v6.md` |
| 8 — Tier-1 new scenes + Tier-4 tightening | Largest structural additions + compression of overgrown passages | `_revised_v7.md` |

**The discipline rule the multi-pass pattern installs:** Each pass has a single dimension. Don't mix "fix historical accuracy" with "improve interpersonal dynamics" — the conflated pass corrupts both objectives. The same prose can be revised eight times without entropic collapse if each pass operates on one axis.

> **Anti-pattern caught and named:** "Mode 6 (spec drift without empirical justification)" — invoking changes without closed-loop evidence. The textverse spec at `docs/spec-v0.128.md` §15.4 formalizes this for code; the same rule applies to prose revisions. A pass that says "I think this should be tighter" without naming the specific failure mode being addressed is the failure mode.

### 1.3 Parallel-instance audit

For *The Night Was Young* Pass 7 (the Rubaiyat pass), a **second Claude instance (Opus 4.7)** was asked to independently audit the work of the first (Opus 4.6).

Source: `PROMPT_FOR_47.md`, `PROMPT_FOR_47_FOLLOWUP.md`. The audit produced three patches that were applied:

1. Capacity-withheld discriminant in two-second evaluation
2. Thermodynamic-fact rewording of "door opens from inside"
3. Weight lean (head on cork lifebelt, one breath)

**The rule:** When a passage carries unusual load, a second instance reading cold (no chat history, only files) catches the things the originating instance has locked into. The cost is one focused prompt + ~30K tokens of file reading. The yield is structural validation that the originating session cannot self-perform.

**For ASTRA-7:** Use the same pattern on any load-bearing passage in *The Long Watch* — feed the relevant chapter + CANON.md + negative_space.md + voice spec to a fresh instance and ask it the equivalent of the three questions: structural audit, missing beat, sufficiency check.

### 1.4 1M context window as primary substrate

All three books were written in Claude Opus 4.6/4.7 sessions with **1M context windows**. The prior workflow was: load the entire manuscript + all source documents + voice spec + research returns into context simultaneously, then revise.

**From `CONTINUATION_PROMPT.md`:** "The prior session held ALL of the above simultaneously in its 1M context window. A new session may need to be selective depending on the task."

**Critical operational fact:** Sessions consume context. The continuation pattern (write a CONTINUATION_PROMPT.md before the session degrades, hand off cold to next instance) was developed because no single session can carry an entire production cycle. *The Night Was Young* used **3 sequential CONTINUATION_PROMPT files** across its production lineage.

### 1.5 The bo-voice SKILL as enforcement layer

The voice specification at `voice\bo-voice\SKILL.md` is invoked when prose is being generated or audited *in Bo's voice* (essays, blurbs, author bios). It is NOT used for fiction prose — fiction prose has its own register that adapts the voice engine to narrative.

**Voice DNA distilled (full spec preserves the detail):**

1. Recursive restatement as argumentative structure (3-6 framings of the same thesis)
2. Maximalist commitments, conditional cascades ending in *necessarily / inevitable / no choice but*
3. Metaphors from physical/mechanical systems — never from literature, pop culture, or business
4. Mixed register — archaic formality (*indeed, alas, thereof, whilst, aforementioned*) braided with colloquialism (*etc etc etc, that guy, no-brainer*)
5. Scale-invariant zoom — cosmic ↔ bodily within paragraphs
6. Compound/doubled/tripled adjective-noun stacks
7. Temporal-existential framing (*into perpetuity, a mere blink of an eye*)
8. Unashamed grandiloquence — no irony shield

**Words to never use (will instantly kill voice):** *delve, nuanced, multifaceted, holistic, leverage* (as verb), *navigate* (as metaphor), *tapestry, landscape* (metaphorical), *journey* (metaphorical), *unpack, dive in, lean into, key takeaways, in summary, TL;DR*. Em-dashes as the primary connective device. Bullet lists in prose contexts.

**Bo-isms to preserve as fingerprint (not "typos"):**
- "underlining" for underlying
- Slash-compounds (*work/force/productivity multiplier-effect*)
- Ellipses as connective tissue (not "trailing off")
- Loose commas, run-ons up to 60+ words

---

## 2. Voice discipline

### 2.1 Anti-LLM-leak prophylaxis

The single largest threat to all three books was sanitization toward generic LLM voice during long sessions. Caught failures:

- "It's worth noting that..." — anywhere
- Em-dashes used as the primary connective beat (Bo uses commas, ellipses, parentheses)
- Balanced "on the one hand / on the other hand" framing
- Bullet points in narrative
- Hedge words (*perhaps, arguably, it could be said*)
- Greeting-card metaphors when a mechanical metaphor is available
- Crisp topic sentences at paragraph heads

### 2.2 Mechanical greps before every build

Before any docx/PDF rebuild, mechanically scan the source markdown for:

```
grep -n "delve\|nuanced\|multifaceted\|holistic\|leverage\|navigate\|tapestry\|unpack" *.md
grep -n " — " *.md          # em-dash audit
grep -n "^[ \t]*[*-] " *.md  # accidental bullet lists
grep -n "TL;DR\|key takeaway\|in summary" *.md
grep -n "it could be said\|one might argue\|on the other hand" *.md
```

A hit on any of these is presumptively a leak — investigate, don't autopatch. Sometimes the word legitimately belongs (a character may "leverage" a mechanical advantage); the grep is a trigger for a human-eye check, not a fix.

### 2.3 The Mode A / Mode B taxonomy

*The Night Was Young* introduced a deliberate prose-mode taxonomy:

- **Mode A** — analytical voice. Recursive cascades, clause-stacking, meaning-making. 90% of the novel.
- **Mode B** — raw perceptual voice. Short declarative sentences, concrete nouns, no subordinate clauses. Deployed at 8 peak emotional moments where the narrator's analytical apparatus fails.

**The discipline:** Mode B never dominates. It is the rare gas that Mode A flows around. The contrast IS the event. When two modes are deliberately scoped, the reader can feel the apparatus shifting; when only one mode exists, the prose is monotone.

**For ASTRA-7:** ASTRA's voice has its own bimodal register (anti-performance "Caught." / "Fair." vs. the longer essayistic stretches at the watching/keeping moments). The same Mode A / Mode B contrast principle applies.

### 2.4 Voice register adapted to character

Maren Cole (*The City and the Girl*) speaks in spatial metaphors because her cognition processes form before language. Her voice is NOT Bo's voice — but it is **a voice engine adjacent to Bo's**: same architecture (recursive restatement, conditional cascades, anti-irony), different lexical surface (technical fabrication vocabulary instead of thermodynamic).

The lesson: the bo-voice spec is the **engine**, not the surface. When writing a character, port the engine, change the lexical fingerprint. *Tori* in *The Night Was Young* and *Maren* in *The City and the Girl* both speak with conditional cascades and refuse irony-shielding, but Tori speaks in clinical-questions-about-emotional-situations cadence while Maren speaks in spatial-engineering metaphors.

---

## 3. Workflow patterns

### 3.1 File organization (the layout that actually worked)

```
C:\Claude-Titanic\                          ← root for all three books
├── PRODUCTION_LESSONS_LEARNED.md           ← seed for this document (outdated values in places)
├── CLAUDE.md                               ← per-project mission briefing
├── CONTINUATION_PROMPT*.md                 ← session-to-session handoff
├── PROMPT_FOR_47*.md                       ← parallel-instance audit prompts
├── generate_book_*.js                      ← docx generators (Node)
├── generate_*_kdp.js / _kindle.js          ← per-book/per-format docx generators
├── composite_cover_*.py                    ← cover image composers (Python/PIL)
├── build_digital_*.py                      ← digital PDF assemblers (Python/PyMuPDF)
├── check_part_pages.py                     ← Word-COM page-position verifier
├── lint_manuscript.py                      ← markdown corruption-signature linter
├── fonts/CormorantGaramond-Light.ttf       ← variable-axis serif (300-700 weight)
├── fonts/CormorantGaramond-Bold.ttf
├── final_outputs/                          ← The Night Was Young production area
│   ├── part[1-5]_revised_v[1-7].md
│   ├── The_Night_Was_Young_*.docx          ← versioned docx outputs
│   ├── The_Night_Was_Young_*.pdf
│   ├── BOOK_COVER_IMAGE_PROMPTS.md
│   ├── BACK_COVER_COPY.md
│   └── KINDLE_LISTING.md / KINDLE_DESCRIPTION_4000.txt
├── the_city_and_the_girl/                  ← per-book directory
│   ├── M0_Soul_Document.md
│   ├── M0_System_Prompt.md
│   ├── part[1-3]_*.md                      ← chapter markdown
│   ├── manuscript.md
│   ├── cover_raw.png                       ← AI-generated source, untouched
│   ├── cover_final.png                     ← composited with title (front only)
│   ├── *.docx / *.pdf
│   └── outputs/
│       ├── kdp_paperback/                  ← format-specific subdirs
│       ├── kdp_hardcover/
│       └── digital/
└── the_second_notebook/
    ├── (similar structure)
    └── outputs/
        ├── kdp_paperback/
        ├── kdp_hardcover/
        ├── kindle/
        └── digital/
```

**Key invariants of this layout:**
- Per-format `outputs/` subdirectories prevent cross-contamination of files with similar names
- AI source art stays in cover_raw.png, never overwritten; cover_final.png is composited on top
- Generators live at the project root and read into per-book directories via absolute paths

### 3.2 Version naming convention

Source markdown evolves through numbered revisions (`part1_revised_v3.md`, `_v4.md`, …). Output docx files are versioned independently (`The_Night_Was_Young_6x9_v10.docx`, `_v11.docx`, …).

**Critical:** Source-version drift between generators is the most common production bug. *The Night Was Young* once shipped a Kindle ebook missing 8,476 words because `generate_kindle.js` was still reading `part*_revised_v6.md` while `generate_book_kdp.js` had been updated to read `v7`.

**Rule:** Every markdown revision pass includes a checklist item — "update source version in ALL generator scripts." Grep all `.js` files for the old version string and update them in lockstep.

### 3.3 Session protocols (CONTINUATION_PROMPT pattern)

Long production cycles span multiple Claude sessions. The handoff document is **CONTINUATION_PROMPT.md** (and `_v2`, `_v3` as cycles compound).

What every CONTINUATION_PROMPT must contain:
- Current state of work (specific files: which is canonical)
- What has been completed (passes done)
- What remains to do (passes pending)
- Key facts a continuing Claude needs (character architecture, voice rules, decisions made)
- How to regenerate (commands, paths, dependencies)
- Open questions / unfinished items

The handoff file is written at ~80% context fill in the originating session, while the originator still has the full context and can articulate what's salient. Written later than that, the originator's compression starts to drop load-bearing detail.

### 3.4 Image handling discipline (from `PRODUCTION_LESSONS_LEARNED.md`)

A prior session died because too many screenshot tool-calls filled the context window. Rule going forward:

- User drops files into `C:\Claude-Titanic\image_input\`
- Claude reads them via the Read tool (disk path)
- Claude writes outputs to a `_output` or project subdirectory
- No image content goes back into chat messages

This kept the whole multi-format production tractable inside a single session window.

### 3.5 The screenshot-to-text pipeline

For UE5-walkthrough or any visual-source pass, intermediate via text:

- Screenshots go in numbered subfolders under `C:\Claude-Titanic\docs\screenshots\`
- Claude reads all images in each folder, writes a `DESCRIPTION.md` in the same folder with per-image descriptions and novel-ready details
- During the final prose pass, Claude reads only the text files — no images needed

First test batch was `7_boatdeckevac/` (8 screenshots, 8 descriptions, pipeline validated). The pattern collapses visual context into textual context once and reuses the textual context for downstream prose passes.

---

## 4. Editing and revision lessons

### 4.1 The manuscript linter

`C:\Claude-Titanic\lint_manuscript.py` codifies seven corruption-signature checks discovered during production. Run before every build. Exit code 1 halts the build.

| Check | Catches |
|---|---|
| `EMBEDDED_UNDERSCORE` | `a_Thursday` — markdown italic markers that survived PDF/DOCX round-trip and were re-interpreted as underlines |
| `PARAGRAPH_NOT_TERMINATED` | Paragraph ends without sentence-ending punctuation → likely PDF-line-wrap flattening mid-sentence |
| `UNBALANCED_EMPHASIS` | Odd count of `_` or `*` in a paragraph (runaway italic) |
| `STRAY_MARKDOWN` | `###` or bullet `-` or `[link](url)` mid-prose |
| `MULTIPLE_SPACES` | Two-plus consecutive spaces inside a line (PDF tab/alignment flattening) |
| `MID_WORD_HYPHEN_BREAK` | `word-\n` followed by lowercase line (PDF soft-hyphen carried through) |
| `EMDASH_CONTINUATION` | Paragraph ending in `—` followed by a paragraph starting lowercase (split sentence across hard break) |

This linter was built **after** *The Second Notebook* shipped with a round-tripped artifact that the build hadn't caught. The rule it installs: round-tripping markdown through a rendered intermediate (PDF, DOCX) and back to text is a corruption attack surface. Lint catches the signatures.

### 4.2 Pass ordering

The empirically-determined order that works:

1. **Structural rewrite** (Pass 0) — never combined with anything else
2. **Phenomenology / fact corrections** (Pass 1) — sweep against research returns
3. **Voice-mode rewrites** (Pass 2) — convert peak moments to Mode B
4. **Late-arriving research** (Pass 4) — if a new source document arrives, sweep with it
5. **Late-arriving biographical/source material** (Pass 5) — if new character info arrives
6. **Thematic integration** (Pass 6) — cross-cutting motifs and callbacks
7. **Single load-bearing comprehension** (Pass 7) — the one passage the book exists to reach
8. **Largest structural additions + final tightening** (Pass 8) — only after 7 has stabilized

**Anti-pattern:** Combining "tighten this passage" with "thread a new motif through" in the same pass produces a passage that is *both* compressed *and* expanded. The seams show.

### 4.3 Word COM as authoritative pagination check

`check_part_pages.py` uses `win32com.client` to open the docx in Word, repaginate, and find each Part heading by text search. Returns page number and parity (recto/verso).

```python
import win32com.client
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
doc = word.Documents.Open(str(DOCX_PATH.resolve()), ReadOnly=True)
doc.Repaginate()
total_pages = doc.ComputeStatistics(2)  # wdStatisticPages = 2
# ...iterate parts by Find.Text...
# page = word_app.Selection.Information(3)  # wdActiveEndAdjustedPageNumber
```

**Why this matters:** No pure-Python or LibreOffice headless route produces page numbers that match what KDP/Mixam will actually print. Word is authoritative because the printers' validators are calibrated against Word's pagination. Anything else lies.

### 4.4 Content-parity check between formats

For multi-format builds (print + Kindle), parity-check word counts:

```python
from docx import Document
for label, p in [("Kindle", kindle_path), ("Hardcover", hardcover_path)]:
    d = Document(p)
    wc = sum(len(r.text.split()) for para in d.paragraphs for r in para.runs)
    print(f"{label:15} {wc:,} words")
```

Body-content parity is the goal. Kindle may be slightly higher due to About-the-Author back matter; that's fine. If Kindle is LOWER, some revision didn't make it across — check the source markdown version in both generators.

---

## 5. Cover design lessons

### 5.1 The three-panel anatomy

Every cover has three panels regardless of platform:
- **Front cover** — 6×9 trim (for 6×9 books), title and author baked
- **Back cover** — 6×9 trim, blurb and (for KDP) ISBN barcode keep-out area
- **Spine** — varies by page count, vertical title and author

Platforms differ in how panels combine:

| Platform | Cover deliverable |
|---|---|
| **Mixam premium** | THREE separate PDFs (`front_cover.pdf`, `back_cover.pdf`, `spine.pdf`) — 0.80" bleed each |
| **KDP paperback** | ONE PDF (single wrap): `[back] [spine] [front]` left-to-right, 0.125" bleed on all four outer edges |
| **KDP hardcover (case laminate)** | ONE PDF (single wrap): same `[back] [spine] [front]` but with 0.708" turn-in instead of 0.125" bleed, and a thicker spine |

### 5.2 Color palette (used across all three books)

Established once, reused with adjustment per book:

| Role | Hex |
|---|---|
| Navy (Night Was Young, ASTRA-7-adjacent) | `#0D1B2A` |
| Umber (Second Notebook, City) | `#120E16` to `#100C12` (slightly different per book) |
| Cream foreground (body color and cover text) | `#F4EFE0` (Titanic) or `#F0EADC` (Second Notebook) |
| Warm cream (back-cover tagline) | `#E4DBC8` |
| Dimmed cream (back-cover bylines/ornaments) | `#AAA094` |
| Gold accent (taglines, ornaments) | `#C9A760` |
| Body text in interior | `#1A1A1A` |

**Match the body-text cream to the cover-text cream** — the visual continuity from cover to body is one of the strongest "this is a real book" signals.

### 5.3 Typography

**Front and back cover typography (all three books):**
- Font: **Cormorant Garamond** (variable axis 300-700 weight)
- Path: `C:\Claude-Titanic\fonts\CormorantGaramond-Light.ttf`
- Load with `f.set_variation_by_axes([weight])` in PIL
- Title weight typically 400-500
- Spine title weight 700, double-drawn with 1px offset for visual bold:

```python
draw_tracked(draw, (title_x, title_y), title, title_font, 0.04, CREAM)
draw_tracked(draw, (title_x + 1, title_y), title, title_font, 0.04, CREAM)  # second pass for weight
```

**Tracking (em-spacing):**
- Title: 0.04 to 0.08 em
- Author byline: 0.10 to 0.12 em (more open)
- Tagline: 0.06 to 0.08 em
- Spine: 0.04 em (compact for narrow spine)

**Sizing formulas (scale to image height):**
- Title size = `int(WRAP_H * 0.075)` — ~7.5% of image height
- Author = `int(WRAP_H * 0.035)` — ~3.5%
- Tagline = `int(WRAP_H * 0.034)`
- Blurb = `int(WRAP_H * 0.0195)`
- Spine title size = `int(SPINE_W_PX * 0.42)` — floor for legibility on narrow spines

### 5.4 Quiet zones (text must stay inside)

**The rule:** Keep typography at least `bleed + 0.25"` from any edge.
- Mixam (0.80" bleed): keep text 1.05" from edges
- KDP paperback (0.125" bleed): keep text 0.375" from edges
- KDP hardcover (0.708" wrap): keep text 0.958" from edges (only need 0.375" inside trim, but plus wrap = 0.958" from outer edge)

**Spine-side quiet zone is wider than other sides** — text near the spine reads cramped because the book bends there. Pad an extra 0.10-0.15" spine-side.

### 5.5 ISBN barcode keep-out (back cover, KDP)

KDP prints the ISBN barcode bottom-right of back cover. Reserve 2.25" × 1.50" of clear space there. Blurb wraps adaptively around the keep-out — switch to narrower text width when the y-cursor descends past the barcode top.

```python
# Adaptive wrap
max_w = back_text_width if (y + line_h) <= barcode_top_y else narrow_text_width
```

### 5.6 Cover-art source preservation

Keep AI-generated / upscaled art at full resolution, untouched, in the cover folder:
- `Gemini_Generated_Image_*.jpg` (source from Gemini Nano Banana)
- `*-topaz-upscale-1.7x.jpg` (Topaz AI upscaled — typically 1.7×)
- `front.jpg`, `back.jpg`, `spine.jpg` (composited panels — title baked)
- `cover_wrap.pdf` etc. (final platform deliverable)

When you change title position or font weight, re-composite from the source, not from the composite. Never lose the source.

### 5.7 PDF MediaBox precision (critical for KDP validator)

KDP's hardcover validator is strict to four decimal places. PIL's `img.save(..., "PDF", resolution=DPI)` often produces a PDF MediaBox that's off by 1/1000". Fix by using PyMuPDF to set the page size explicitly:

```python
import fitz
target_w_pts = WRAP_W_IN * 72
target_h_pts = WRAP_H_IN * 72
pdf = fitz.open()
page = pdf.new_page(width=target_w_pts, height=target_h_pts)
page.insert_image(page.rect, filename=str(out_jpg))
pdf.save(str(out_pdf), deflate=True, garbage=3)
```

This was the only reliable route to get KDP's hardcover dimension validator to pass without iterations.

### 5.8 Front-cover composition philosophy

**The front cover gets the AI-art image at full strength.** Title baked in cream over the image. Author at the bottom, well inside the quiet zone.

For *The Night Was Young*: "BO CHEN" originally at `0.07 × 10.60"` from bottom = 0.74" — INSIDE the 0.80" Mixam bleed. Trimmed off. Fix: `0.13 × 10.60"` = 1.38" from bottom, well inside the quiet zone.

### 5.9 Back-cover composition philosophy

**The back cover gets the SAME AI-art image, darkened to ~75% black** (alpha 184/255). Tagline in gold at top, pull quote in cream beneath, blurb body in cream, byline at bottom. This maintains visual unity front-to-back while letting text be legible.

```python
overlay = Image.new("RGBA", (back_w, back_h), (0, 0, 0, 184))
back_panel = Image.alpha_composite(back_panel, overlay).convert("RGB")
```

### 5.10 Spine composition philosophy

**The spine is solid color (no image)**, navy or umber depending on book. Title horizontally rotated -90° (clockwise) so it reads top-to-bottom when the book stands upright on a shelf. Title + ornament (✦) + author, centered between title-top and bottom turn-ins.

For narrow spines (<0.5"), reduce the ornament size and increase title weight (700) with double-draw offset. For wider spines (>0.6"), the ornament can be ~30% of spine width.

### 5.11 AI cover art workflow

Pipeline that worked across all three books:
1. **Generate** with Gemini Nano Banana (or current SOTA text-to-image)
2. **Upscale** with Topaz AI (1.7× to 4×; Bo runs this offline)
3. **Composite** title text via the project's `composite_cover.py` or per-book variant
4. **Verify** by visual inspection — does the title land on a quiet patch of image? Is the contrast adequate?

When the title sits over a busy patch of image, **darken the underlying region** before drawing text, or shift the title position vertically. Don't add a drop shadow or text-background; those break the literary register.

---

## 6. Paperback formatting lessons

### 6.1 KDP paperback canonical specs (6×9 trim)

Established and re-used across all three books:

| Setting | Value |
|---|---|
| Trim size | 6.00" × 9.00" |
| Paper | Cream (premium for literary fiction; white for technical) |
| Spine width (cream) | `pages × 0.0025` |
| Spine width (white) | `pages × 0.002252` |
| Bleed | 0.125" on all four outer edges (for full-bleed covers) |
| Gutter (inside / spine-side margin) | 0.625" |
| Outside margin | 0.5" |
| Top margin | 0.5" |
| Bottom margin | 0.625" |
| Mirror margins | **REQUIRED** for proper recto/verso layout |
| Page count multiple | **2** |
| Body font | Georgia 11pt (typical) or 12pt for shorter books |
| Body line spacing | 320 DXA (~1.35×) for 11pt, 340 DXA (~1.4×) for 12pt |
| First-line indent | 360 DXA (~0.25") |
| Body color | `#1A1A1A` (not pure black — easier on the eye) |
| Justification | `AlignmentType.JUSTIFIED` |

### 6.2 Mixam premium hardcover canonical specs (6×9 trim)

| Setting | Value |
|---|---|
| Trim | 6.00" × 9.00" |
| Interior bleed | 0.125" |
| Gutter | 0.875" (looser than KDP) |
| Outside | 0.625" |
| Top | 0.625" |
| Bottom | 0.75" |
| Cover bleed | 0.80" on all four sides — **unusual; this is Mixam-specific** |
| Page count multiple | **4** |
| Spine | Mixam gives you an exact spine number in their job spec; we used a separate `spine.jpg` panel |
| Font | Georgia 12pt, body color `#1A1A1A` |
| Line spacing | 340 DXA (~1.4×) |

**The page-count delta:** Same source markdown rendered with Mixam's looser margins comes out to ~204pp; same markdown with KDP's tighter margins comes out to ~185pp. **You CANNOT reuse covers across services** — the spine width is different, and the front/back trim handling is different.

### 6.3 Mirror margins (THE single biggest docx gotcha)

`docx@9` (Node library) silently drops the per-section mirror flag. The fix is **post-process injection into settings.xml via JSZip**:

```javascript
const JSZip = require("jszip");
Packer.toBuffer(doc).then(async buffer => {
  const zip = await JSZip.loadAsync(buffer);
  let settings = await zip.file("word/settings.xml").async("string");
  if (!settings.includes("mirrorMargins")) {
    settings = settings.replace("</w:settings>", "  <w:mirrorMargins/>\n</w:settings>");
  }
  zip.file("word/settings.xml", settings);
  const finalBuffer = await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  fs.writeFileSync(outPath, finalBuffer);
});
```

Without this injection, the docx looks correct in Word preview but prints with a constant gutter (text crawls into the spine on alternate pages). Always inject. Always re-verify in Word's actual print preview.

### 6.4 Per-section page numbering

The body section needs `pageNumbers: { start: 1 }` to restart numbering at the first body page (skipping front matter). Footers use mirror-aligned page numbers — RIGHT-aligned on recto (default footer), LEFT-aligned on verso (even footer):

```javascript
footers: {
  default: new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "888888" })],
    })],
  }),
  even: new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.LEFT,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "888888" })],
    })],
  }),
},
```

### 6.5 Front matter pagination (recto/verso discipline)

Physical books traditionally start each Part on a recto (right-hand, odd-numbered) page.

**Canonical front matter sequence (for hardcover):**
```
Page 1-2 — cover (Mixam/printer handles separately, not in interior file)
Page 3 (recto) — Half-title
Page 4 (verso) — Blank
Page 5 (recto) — Full title page
Page 6 (verso) — Copyright (positioned at BOTTOM of page, traditional)
Page 7 (recto) — Dedication
Page 8 (verso) — Blank
Page 9 (recto) — Epigraph
Page 10 (verso) — Blank
Page 11 (recto) — Part I begins
```

**For paperback (slimmer convention):**
```
Page i (recto) — Half-title
Page ii (verso) — Blank
Page iii (recto) — Full title page
Page iv (verso) — Copyright
Page 1 (recto) — Body begins (page numbers restart at 1)
```

**Key invariant:** every Part's first page has an odd page number when viewed in the finished book. If a Part lands on verso, insert a blank verso before it.

### 6.6 Running header

Body section has a centered running header in the same font as the body, at ~75% of body size, in a muted gray (`#AAAAAA` or `#888888`):

```javascript
headers: {
  default: new Header({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "THE NIGHT WAS YOUNG", font: FONT, size: 15, color: "AAAAAA", characterSpacing: 30 })],
    })],
  }),
},
```

No header on front matter pages. No header on Part-opening pages (some setups; depends on aesthetic — both *The Night Was Young* and *The City and the Girl* used a continuous header).

### 6.7 Part heading styling

Centered, all-caps, spaced from top by ~2400 DXA (1.67"), ornament beneath. Use `HeadingLevel.HEADING_1` for Kindle TOC compatibility (the print version doesn't NEED Heading 1, but using the same generator with a single switch for ebook makes maintenance simpler).

```javascript
new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 100, after: 200 },
  alignment: AlignmentType.CENTER,
  children: [new TextRun({
    text: title, font: FONT, size: 24, color: BODY_COLOR, characterSpacing: 80,
  })],
})
```

### 6.8 Section break ornament (within-chapter)

For scene transitions within a chapter, centered ornament:

```javascript
new Paragraph({
  spacing: { before: 240, after: 240 },
  alignment: AlignmentType.CENTER,
  children: [new TextRun({
    text: "\u00B7  \u00B7  \u00B7",   // " ·  ·  · " — three middle dots, double-spaced
    font: "Segoe UI Symbol", size: 18, color: "999999",
  })],
})
```

Other books use `\u2726` (black four-pointed star — ✦) instead of dots. Pick one and use it consistently within a book.

### 6.9 Trailing EVEN_PAGE blank gotcha

KDP's margin validator is strict about ANY rendered content touching the margin boundary, including empty paragraph cursor positions. An empty `<w:p/>` paragraph renders with the text cursor at the paragraph's alignment origin — which for default (left-aligned) sits at x=0.5" on a verso with mirror, i.e. exactly at the outside-margin boundary. KDP flags that as "text outside the margins" even though visually nothing is drawn.

**Fix:** Center-align the empty paragraphs on the trailing blank page so the cursor sits at the middle of the text block. Also override the body section's footer inheritance with explicit empty (center-aligned) footers so no page number leaks onto this page. Use extra-generous margins on the trailing section.

```javascript
{
  properties: {
    type: SectionType.EVEN_PAGE,
    page: {
      size: { width: PAGE_W, height: PAGE_H },
      margin: {
        top: 1440, bottom: 1440, left: 1440, right: 1440,
        header: 0, footer: 0, gutter: 0,
      },
      mirror: true,
    },
  },
  footers: {
    default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER })] }),
    even:    new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER })] }),
  },
  children: [new Paragraph({ alignment: AlignmentType.CENTER })],
}
```

### 6.10 Word COM as the only reliable docx→PDF converter

Pandoc, LibreOffice headless, docx2pdf-cloud — all produced bad PDFs (font substitution, broken TOC hyperlinks, mis-paginated headers). Only Microsoft Word via `win32com.client` preserved the layout faithfully.

```python
import win32com.client
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
doc = word.Documents.Open(str(DOCX_PATH.resolve()))
doc.SaveAs(str(PDF_PATH.resolve()), FileFormat=17)  # 17 = wdFormatPDF
doc.Close(SaveChanges=False)
word.Quit()
```

Requires Windows + installed Word. That's fine for Bo's setup but will NOT work on a Mac/Linux environment.

---

## 7. Hardcover formatting lessons

### 7.1 KDP hardcover (case laminate)

Case laminate = the printed image is laminated directly onto the cardboard case. No dust jacket. Image visible directly on the book.

**Wrap math (the rule that took multiple rejections to learn):**

> KDP hardcover is NOT the same as KDP paperback with more bleed.

The printed sheet WRAPS around two rigid cardboard boards (front + back) joined by a spine board:
- You need **0.708" of extra material on every outer edge** (not 0.125")
- The **spine is wider** than the paperback equivalent — the boards add thickness

| Paper × Pages | Paperback wrap | Hardcover wrap | Hardcover spine |
|---|---|---|---|
| Cream × 100pp | 12.385" × 9.25" / spine 0.25" | 14.014" × 10.417" / spine 0.598" | (paperback spine + 0.348") |
| Cream × 104pp | 12.510" × 9.25" / spine 0.260" | 14.024" × 10.417" / spine 0.608" | (paperback spine + 0.348") |
| Cream × 186pp | 12.715" × 9.250" / spine 0.465" | 14.183" × 10.416" / spine 0.767" | (paperback spine + 0.302" per old notes; +0.348" per newer code — see §17) |

**KDP's expected dimensions (validator-checked to 4 decimal places):**
- Width = `(6 × 2) + spine_with_boards + (0.708 × 2)`
- Height = `10.417"` (KDP uses this exactly; arithmetic `9 + 0.708×2 = 10.416` and KDP rounds up)

**Always use the round-up height (10.417") not the arithmetic (10.416").** The validator checks the rounded number.

### 7.2 Mixam premium hardcover (case wrap / case-bound-with-dust-jacket variant)

Mixam's premium hardcover comes in two binding flavors:
- **Smyth Sewn** — preferred, premium aesthetic, longer ship time
- **Adhesive Casebound** — speed compromise, glued

Lamination:
- **Matte** — preferred, literary
- **Gloss** — speed compromise, more reflective

**Mixam-specific spec for the 6×9 / 70lb / 204pp build (used for *The Night Was Young*):**
- Hardcover Novels, 6×9, **204 pages**, Portrait, **70lb Text Uncoated**
- **Adhesive Casebound** or Smyth Sewn (choose)
- **Gloss Lamination** or Matte
- Stock White endpapers
- Navy Blue bookmark ribbon, Navy Blue & White head/tail band
- **NO dust jacket** (cover artwork prints directly on hardcover boards) — but Mixam supports the dust jacket variant if you want one
- **Spine: 0.67"** (Mixam-calculated from 204pp × 70lb)

Mixam gives you the spine number in their job spec after upload of the interior. **Do not pre-compute** — let Mixam tell you the spine width, then build the cover.

### 7.3 Dust jacket (for hardcover-with-DJ variants)

The *The Night Was Young* artifact directory at `the_night_was_young_cover\` includes both a wrap-style cover (printed directly on boards) and a separate set of files for the dust jacket variant. Files:
- `Gemini_Generated_Image_*.jpg` — source AI art
- `front.jpg`, `back.jpg`, `spine.jpg` — composited panels
- `cover_wrap.pdf` (single combined for KDP) and separate `front_cover.pdf`, `back_cover.pdf`, `spine.pdf` for Mixam

For a dust jacket specifically, the spec varies more by printer; check the printer's template.

### 7.4 Endpapers

For hardcover books, endpapers can be:
- **Stock white** (default, cheap)
- **Custom-printed** with a design (e.g., "amber-on-navy deck plans" was the *The Night Was Young* concept — never produced)

If you want printed endpapers, generate them as a separate PDF at 6×9 trim (or whatever the printer's spec is) and submit alongside the cover and interior.

### 7.5 Head/tail bands and bookmark ribbon

Mixam's premium hardcover offers:
- Head/tail bands (the woven cloth at the top and bottom of the spine where pages meet binding) — choose color
- Bookmark ribbon — choose color

For *The Night Was Young*: Navy Blue bookmark ribbon, Navy Blue & White head/tail band. Match the cover palette.

KDP hardcover does NOT offer head/tail bands or bookmark ribbon. If those matter, use Mixam (or IngramSpark — not yet tested in this corpus, see §17).

---

## 8. KDP-specific lessons

### 8.1 KDP Print Previewer

**The KDP Print Previewer is authoritative.** If a cover or interior passes the previewer, it will pass review. If it fails the previewer, the error message tells you the EXACT expected dimensions — use those literally:

> Example error from a real KDP rejection: *"Your expected cover size is 14.183×10.417 but the submitted file size is 12.713×9.250."*

That error was the pivotal moment that established the correct KDP hardcover wrap math.

### 8.2 KDP cover spine formula (cream paper, 2026 era)

- Paperback: `SPINE_IN = PAGES × 0.0025`
- White: `PAGES × 0.002252`
- Hardcover adds boards: `+ 0.302"` (per old `PRODUCTION_LESSONS_LEARNED.md`) OR `+ 0.348"` (per the newer `composite_cover_*_kdp_hardcover.py` scripts, calibrated empirically against Print Previewer rejections on the Autotelic Disposition build)
- **See §17 contradictions — use 0.348" unless previewer rejects, then revise**

### 8.3 KDP page-count multiple

KDP interior PDFs must have an **even** page count (multiple of 2). Round up to the next even number with a blank verso at the end if needed.

### 8.4 KDP file requirements

- **Interior:** PDF or DOCX. PDF preferred (control over fonts). Generated via Word COM as in §6.10.
- **Cover:** PDF, single-wrap (back + spine + front in one file). The cover dimensions depend on whether paperback or hardcover.

### 8.5 KDP linking paperback to existing Kindle

If you already have a Kindle listing on KDP, adding a hardcover format to the same title automatically links them. You don't create a new title — you add a new format to the existing one.

### 8.6 KDP Kindle is in a separate workflow

The same author dashboard, but Kindle ebooks have entirely separate file specs (see §10). Don't mix them.

### 8.7 KDP review timing

Books are reviewed in 1-3 business days. If the previewer passes, review passes ~100% of the time. If the previewer fails, fix and re-upload — don't submit, because the human reviewer will reject and you lose a cycle.

### 8.8 KDP Kindle updating-after-publish

Updates to a live Kindle ebook do NOT auto-push to existing buyers. Amazon keeps existing customers on the version they purchased. They must opt in via "Manage Your Content and Devices" → "Update Available". For substantial revisions, you can request Amazon proactively push via the KDP Help > Update Content form. New buyers always get the latest.

### 8.9 KDP paperback proof copies

Order proof copies before mass publishing — they're sold to you at print cost (about $5-8 for a paperback). Hold them, smell them, feel the binding. The PDF doesn't tell you whether the spine looks right. Physical proof does.

---

## 9. Mixam-specific lessons

### 9.1 Mixam filename auto-routing (THE gotcha)

Mixam's upload form silently parses filenames looking for keywords to route each PDF to the correct slot. If you upload `back.pdf`, it interprets "back" as "back of the interior" → puts it on Body Page 1 of the book block. You get no warning.

**Keyword routing rules (discovered empirically):**

| Keyword in filename | Routes to |
|---|---|
| `front` | Front cover |
| `back` (alone, no other qualifier) | **Interior body**, NOT back cover |
| `back_cover`, `rear_cover`, `outer_back_cover` | Outer back cover ✓ |
| `inner` | Interior body ✓ |
| `spine` | Spine |

**Fix:** Name cover files `front_cover.pdf`, `back_cover.pdf`, `spine.pdf`. Name body file `inner_*.pdf`.

The cover folder at `C:\Claude-Titanic\the_night_was_young_cover\` contains the empirical record: `back.pdf`, `back_cover.pdf`, `cover_back.pdf`, `outer_back_cover.pdf`, `outercover_back.pdf`, `rear_cover.pdf` — all multiple attempts to find a name that routed correctly.

### 9.2 Mixam bleed convention

**0.80" bleed on all four sides** of the cover (unusual; most printers use 0.125"). The interior also uses different bleed: 0.125".

The bleed on Mixam covers is wide because they trim from a larger sheet and the trim variance is greater. Build cover artwork that extends fully into the bleed — never let the trim line cross a critical typography element.

### 9.3 Mixam interior page-count multiple

Mixam requires multiples of **4** (not 2 like KDP). Round up to nearest multiple of 4 with blank pages at the end.

### 9.4 Mixam spine calculation

Mixam gives you the exact spine number in their job spec after you upload the interior. Don't pre-compute. Build the cover only after Mixam has told you the spine width.

### 9.5 Mixam premium quality vs. KDP

Mixam prints noticeably better than KDP — paper quality, color accuracy, binding feel. But:
- Mixam ships from the UK (longer transit)
- Mixam costs ~3-5× more per copy
- Mixam doesn't have Amazon's distribution

**Use Mixam for the author's personal copies and gift copies; use KDP for the public-facing edition unless premium quality matters for marketing.**

### 9.6 Mixam Adhesive vs. Smyth Sewn

| Binding | Pros | Cons |
|---|---|---|
| **Smyth Sewn** | Premium, lays flat, durable | Longer ship time |
| **Adhesive Casebound** | Faster, cheaper | Doesn't lay as flat, less durable for heavy use |

For *The Night Was Young*, Bo chose Adhesive for speed. Document the choice and rationale; don't pretend Smyth Sewn is always worth it.

### 9.7 Mixam lamination

| Lamination | Pros | Cons |
|---|---|---|
| **Matte** | Literary, soft-touch | Slightly less protective |
| **Gloss** | More photo-vivid, more durable | Reflective; reads as commercial |

For literary fiction, matte is the default. Glossy reads as airport-thriller.

---

## 10. Kindle ebook lessons

### 10.1 Kindle spec at a glance

| Concern | Rule |
|---|---|
| Format | `.docx` preferred (also `.epub`, `.kpf`) |
| Page count | **MEANINGLESS** — Kindle reflows. Amazon displays an estimated count from word count, not your file. |
| Page numbers | **Forbidden** — no footer with PageNumber |
| Running headers | **Forbidden** |
| Mirror margins | **Forbidden** — it's a print concept |
| Blank versos | **Forbidden** — reader sees empty screens mid-story |
| Forced rectos | **Forbidden** |
| Chapter delimiters | `new Paragraph({ children: [new PageBreak()] })` — Amazon uses these as chapter boundaries |
| Navigable TOC | `new TableOfContents(...)` with `hyperlink: true` |
| Auto-TOC scan | Apply **Heading 1** style to chapter titles — Amazon scans for H1 |
| Body font | Suggestion only — readers can override |
| Code spans | Tag as `Consolas` — Kindle uses its own monospace |
| Back matter | About the Author helps discoverability; print often omits |

### 10.2 Do NOT try to match the ebook's page count to the print version

"Make it 204 pages" is the wrong framing. The 18-page gap between an ebook and its hardcover is entirely print-specific formatting (half-title + blank verso + title + copyright + dedication + blank + epigraph + blank + forced rectos + multiple-of-4 padding). Every one of those is a **physical-book convention** that looks broken in a reflowable Kindle. What you actually want is **content parity** — same narrative words, regardless of how each format paginates them.

### 10.3 Parser asymmetry between ebook and print generators

`generate_book_kdp.js` (print) handles both code spans (backticks) AND italics (asterisks). The older `generate_kindle.js` only handled italics — so a Torricelli equation written as `` `Q = Cd * A * sqrt(2 * G * H)` `` survived in the hardcover but silently rendered in the ebook with the backticks visible. Fix: make both parsers symmetric. Split on backticks FIRST, then italics within non-code segments. See `generate_kindle.js` lines ~68-95 for the now-correct version:

```javascript
function createBodyParagraph(text) {
  const runs = [];
  // Split on code spans (backticks) FIRST so asterisks inside code are not consumed as italics.
  const codeParts = text.split(/(`[^`]+`)/g);
  for (const codePart of codeParts) {
    if (codePart.startsWith("`") && codePart.endsWith("`") && codePart.length > 2) {
      runs.push(new TextRun({
        text: codePart.slice(1, -1),
        font: "Consolas", size: BODY_SIZE, color: BODY_COLOR,
      }));
    } else if (codePart.length > 0) {
      const italicParts = codePart.split(/(\*[^*]+\*)/g);
      for (const part of italicParts) {
        if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
          runs.push(new TextRun({ text: part.slice(1, -1), italics: true, ... }));
        } else if (part.length > 0) {
          runs.push(new TextRun({ text: part, ... }));
        }
      }
    }
  }
  return new Paragraph({ ... });
}
```

### 10.4 Equation rendering (Kindle)

The About-the-Author bio in *The Night Was Young* includes `η(r) = 1 − 1/r` rendered via Cambria Math font. Kindle handles math fonts decently IF they're tagged with a font name. Without an explicit font, Kindle may substitute and break the glyph. Always specify `font: "Cambria Math"` (or equivalent) for math characters.

```javascript
new TextRun({ text: "\u03B7(r) = 1 \u2212 1/r", font: "Cambria Math", size: 26, color: BODY_COLOR, italics: true })
```

### 10.5 Auto-generated TOC

Build a navigable Kindle TOC from Heading 1 styles:

```javascript
children.push(new TableOfContents("Table of Contents", {
  hyperlink: true,
  headingStyleRange: "1-1",
  stylesWithLevels: [new StyleLevel("Heading1", 1)],
}));
```

And enable `features: { updateFields: true }` on the Document so the TOC auto-updates when opened.

### 10.6 Front matter for Kindle (lean)

```
[Title page]      — same as print title page, optional
[Copyright page]  — minimal, no dedication of full ceremony
[Dedication]      — optional
[Epigraph]        — optional
[TOC]             — auto-generated from H1
[Part I...]       — body
[About the Author] — back matter for discoverability
```

No half-title (print convention). No blank pages. Page breaks before each Part are encoded as `new PageBreak()` paragraphs — Amazon uses these as chapter boundaries for navigation.

### 10.7 Single-section docx (no mirror, no headers/footers)

Kindle docx is one section, no headers, no footers, no mirror margins, no page numbers. Margins are tokenized as 1" all sides (suggestion — Kindle ignores).

```javascript
sections: [{
  properties: {
    page: {
      margin: {
        top: 1440, bottom: 1440, left: 1440, right: 1440,
        header: 0, footer: 0, gutter: 0,
      },
    },
  },
  children: children,
}],
```

NO JSZip post-processing needed (no mirror margins).

---

## 11. Digital PDF distribution lessons

### 11.1 The pattern (built and reused for all three books)

Single-file PDF for email / Google Drive distribution:
- Page 1: Front cover (6×9 trim only, no bleed)
- Page 2: Back cover (6×9 trim only)
- Pages 3+: Interior body (with print front-matter that duplicates the covers stripped)

### 11.2 Cropping covers from bleed back to trim

The Mixam/KDP covers have bleed baked in. Strip it:

```python
BLEED_PX = int(0.80 * DPI)  # 240 px — Mixam cover bleed
# OR for KDP:
BLEED_PX = int(0.125 * DPI)  # 37.5 px

cropped = img.crop((BLEED_PX, BLEED_PX, img.width - BLEED_PX, img.height - BLEED_PX))
```

### 11.3 Stripping interior front matter that duplicates covers

The print interior has a half-title + title page + copyright that the digital reader doesn't need (the cover already shows the title). Strip those pages by 1-indexed page number:

```python
FRONT_MATTER_TO_STRIP_1IDX = {2, 3, 4}  # blank verso, title page, copyright
```

Keep the half-title (page 1) as a quiet divider between covers and body.

### 11.4 Stripping all-blank body pages

ODD_PAGE recto enforcement inserts blanks before each Part. The print needs them; the digital reader doesn't:

```python
def identify_blank_pages(pdf_path: Path) -> list[int]:
    doc = fitz.open(pdf_path)
    blanks = []
    for i in range(len(doc)):
        text = doc[i].get_text().strip()
        imgs = doc[i].get_images()
        if len(text) == 0 and not imgs:
            blanks.append(i)
    doc.close()
    return blanks

strip_0idx = set(blanks_0idx) | set(front_matter_0idx)
```

### 11.5 Building covers as proper-MediaBox PDFs via PyMuPDF

Use PyMuPDF (`fitz`) so the digital PDF has exact 6×9 MediaBox pages for the covers, matching the trim of the body pages:

```python
page_w_pts = TRIM_W_IN * 72
page_h_pts = TRIM_H_IN * 72
out = fitz.open()
p_front = out.new_page(width=page_w_pts, height=page_h_pts)
p_front.insert_image(p_front.rect, filename=str(front_tmp))
```

### 11.6 Final assembly via PyPDF2 or PyMuPDF

PyMuPDF supports both reading and writing; concatenate:

```python
out.insert_pdf(src, from_page=i, to_page=i)  # for each kept page
out.save(str(OUT_PDF), deflate=True, garbage=4, clean=True)
```

Or PyPDF2:

```python
writer = PdfWriter()
for pdf_path in [TMP_FRONT, TMP_BACK, KDP_PDF]:
    with open(pdf_path, "rb") as f:
        r = PdfReader(f)
        for p in r.pages:
            writer.add_page(p)
with open(OUT_PDF, "wb") as f:
    writer.write(f)
```

Both work. PyMuPDF gives more control over compression.

### 11.7 Typical digital file size

For a ~50K-word novel with ~200-page interior: **1-2 MB** with `deflate=True, garbage=4, clean=True` compression. Significantly smaller and slower to share if compression is omitted.

---

## 12. Platform comparison

### 12.1 KDP vs. Mixam (the trade-off matrix)

| Dimension | KDP | Mixam |
|---|---|---|
| **Cost per copy (1-2 units)** | $4-8 paperback, $14-22 hardcover | $20-50 hardcover |
| **Print quality** | Good (2025-2026 era) | Excellent |
| **Binding quality** | Standard | Premium options (Smyth Sewn) |
| **Color accuracy** | Solid | Better |
| **Ship time** | 3-5 days US | 1-2 weeks UK→US |
| **Reach** | Amazon's global distribution | Print-only, no distribution |
| **File format** | Single-wrap PDF | Three separate PDFs |
| **Bleed convention** | 0.125" (cover), 0.125" (interior) | 0.80" (cover), 0.125" (interior) |
| **Page count multiple** | 2 | 4 |
| **Cover dimensions** | Strict to 4 decimal places | More forgiving |
| **Spine calculation** | Author computes | Mixam tells you |
| **Bookmark ribbon / head/tail bands** | No | Yes (premium hardcover) |
| **Dust jacket variant** | No | Yes |
| **Royalty** | Author-friendly | None (just print cost) |
| **Workflow latency** | Hours | Days |

### 12.2 When to use each

- **KDP paperback** — always, for public availability and royalty
- **KDP hardcover** — when you want hardcover on Amazon's distribution; quality is now genuinely good (2025-2026 era)
- **Mixam premium hardcover** — for author's personal copies, gift copies, archival-quality copies; not for the public-facing edition unless premium aesthetic is marketing-relevant
- **Kindle** — always, for ebook discoverability

### 12.3 IngramSpark — NOT IN THIS CORPUS

The three books in this corpus did NOT use IngramSpark. There are no IngramSpark-specific lessons captured here. The seed file (`PRODUCTION_LESSONS_LEARNED.md`) does not mention it. **For *The Long Watch*, if IngramSpark is a candidate platform (for library/bookstore distribution), establish a new lessons-learned section for it after the first IngramSpark build.**

What's known generically (NOT validated in this corpus):
- IngramSpark reaches the library and bookstore distribution channel (Ingram is the major distributor)
- IngramSpark uses different cover specs than KDP (bleed, spine math)
- IngramSpark has returnability options (paid by author) that KDP doesn't
- IngramSpark has higher upfront fees ($49 setup unless waived) and stricter file validation

---

## 13. Metadata and marketing

### 13.1 Book description engineering

For Kindle listings, the converged pattern across instances:
- **Lyrical hook** (1-2 sentences that match the novel's voice register)
- **Structural thesis** (what the book is about, in the book's terms)
- **Positioning line** (where it sits in the literary landscape — comp titles, register)

For *The Night Was Young*, this was converged from two Claude instances (4.6 and 4.7) plus a Gemini Deep Think instance and saved to `final_outputs/KINDLE_LISTING.md` and `final_outputs/KINDLE_DESCRIPTION_4000.txt`.

**Length:**
- Amazon Kindle listing description: up to 4000 characters (use it)
- Back-cover blurb: 150-200 words for readability
- Hook tagline (front of back cover): 4 short lines, all-caps, gold

### 13.2 Categories and keywords

- **Categories:** 2 max per KDP listing (e.g., Literary Fiction + Historical Fiction > 20th Century)
- **Keywords:** 7 slots — fill them all; optimize for discoverability without keyword-stuffing
- **BISAC codes:** Used for classification; not detailed in this corpus

### 13.3 Back-cover tagline pattern

```
MATHEMATICAL CERTAINTY
WAS THE ONE CARGO
THE TITANIC WAS NOT
EQUIPPED TO CARRY.
```

Four short lines, all-caps, gold (`#C9A760`), tracked at 0.06-0.08 em, centered. Above the pull quote and the body blurb. This single tagline is often what sells the book in 2 seconds.

### 13.4 Author bio

Short version (cover): one paragraph, third person.
Long version (Kindle About the Author back matter): up to 4 paragraphs. *The Night Was Young* uses ~4 paragraphs that close with a load-bearing equation (`η(r) = 1 − 1/r`) — the author bio doubles as a thematic resonance.

**Don't include an author photo if the author is camera-shy** — Bo's bio has no photo.

### 13.5 Amazon A+ content

Not used in this corpus. Could be added for the public-facing edition.

### 13.6 Goodreads

Not used in this corpus.

### 13.7 ISBN

KDP gives you a free ISBN when you publish a paperback or hardcover. The ISBN belongs to Amazon (technically), which limits your ability to use the same ISBN with other distributors. If you want full ownership (and IngramSpark distribution), purchase ISBNs from Bowker (US) at $125-295 each (a 10-pack is cheaper per unit). Not in this corpus's experience.

---

## 14. Pricing and royalties

This section is thin in the corpus — no explicit royalty calculations were preserved in the production lessons. What's known:

### 14.1 KDP royalty structure (general)

- **Kindle:** 70% on $2.99-$9.99 books; 35% on others
- **Paperback:** 60% royalty - print cost. Print cost scales with page count and color/B&W
- **Hardcover:** 60% royalty - print cost. Higher print cost than paperback

### 14.2 Typical print costs (2025-2026 era, 6×9 cream B&W)

- Paperback ~190 pages: ~$4.50 print cost; $15 retail = ~$4.50 royalty
- Hardcover ~190 pages: ~$8.50 print cost; $25 retail = ~$6.50 royalty

### 14.3 The bigger lesson

**Pricing is a marketing decision, not a math decision.** *The Night Was Young* and *The City and the Girl* were not optimized for revenue — they were optimized for the existence of a hardcover artifact and Kindle availability for readers who wanted them. If a future book is intended to generate revenue, the pricing strategy is a separate research project (not captured here).

---

## 15. Common mistakes and gotchas

This is the consolidated gotcha catalog — every named failure mode the corpus documents. Most reference earlier sections.

### G1. Mixam filename auto-routing (§9.1)

Naming a back-cover file `back.pdf` routes it to interior body, not back cover. Use `back_cover.pdf` or `rear_cover.pdf`.

### G2. KDP hardcover ≠ KDP paperback with more bleed (§7.1)

Hardcover needs 0.708" turn-in (not 0.125" bleed) AND a wider spine (+0.302" or +0.348" depending on which calibration is current — see §17).

### G3. Margins changed → page count changed → spine changed → cover invalidated (§5.1)

Anytime interior margins change, regenerate the cover. Never reuse covers across services (Mixam vs. KDP) — the spine widths differ.

### G4. Word COM is the only reliable docx→PDF converter (§6.10)

Pandoc, LibreOffice headless, docx2pdf-cloud all produce bad PDFs. Use `win32com.client`.

### G5. Spine text requirements on a narrow spine (§5.3)

For 6×9 books at <200 pages, the spine is narrow (0.4-0.8"). Title text must be large (`int(spine_width_px × 0.42)` floor) AND bold (weight 700, double-drawn with 1px offset). Tracking ~0.04 em.

### G6. Author byline in cover bleed zone (§5.4)

Keep typography at least `bleed + 0.25"` from any edge. *The Night Was Young* originally had "BO CHEN" at 0.74" from bottom, inside the 0.80" Mixam bleed. Trimmed off.

### G7. Front matter must keep Parts on recto (§6.5)

Count front-matter pages; if a Part would fall on verso, insert a blank verso before it.

### G8. Digital PDF — crop covers from bleed back to trim (§11.2)

For the digital PDF (email distribution), strip the 0.80" (Mixam) or 0.125" (KDP) bleed.

### G9. Cover-art source preservation (§5.6)

Keep AI-generated art at full resolution, untouched, separate from the composite. Never lose the source.

### G10. Image handling discipline — never inline in chat (§3.4)

Read images from disk paths; never paste them into chat messages. Context window dies otherwise.

### G11. Don't match ebook page count to print (§10.2)

Kindle is reflowable; page count is meaningless. Don't add blank versos.

### G12. Parser asymmetry between ebook and print (§10.3)

Code spans (backticks) must be split BEFORE italics. Asymmetric parsers produce different output in different formats from the same markdown.

### G13. Source-version drift between generators (§3.2)

All generator scripts must read the same source version. Grep all `.js` files when revising markdown.

### G14. Kindle content updates don't auto-push to buyers (§8.8)

Existing customers stay on the version they bought unless they opt in. Request proactive push for substantial revisions.

### G15. Equation rendering on Kindle (§10.4)

Explicit `font: "Cambria Math"` for math characters; otherwise Kindle substitutes.

### G16. Mirror margins silently dropped (§6.3)

`docx@9` drops the per-section mirror flag. Post-process inject `<w:mirrorMargins/>` via JSZip into `word/settings.xml`.

### G17. Trailing EVEN_PAGE blank trips KDP margin validator (§6.9)

Empty paragraph cursor on a trailing blank page sits at margin boundary. Center-align the paragraph and use extra-generous margins on that section.

### G18. KDP hardcover height — 10.417" not 10.416" (§7.1)

Arithmetic gives 10.416, KDP uses 10.417. The validator checks the rounded number. Use 10.417.

### G19. PIL `img.save("...", "PDF")` produces imprecise MediaBox (§5.7)

KDP's 4-decimal precision check fails. Use PyMuPDF (`fitz`) to set the page size explicitly.

### G20. Same-session rule: regenerate ALL formats after every markdown revision (§3.2)

If you edit markdown, regenerate hardcover, paperback, Kindle, digital — all of them — before closing the session. Mixed-version distribution is the April 20 *The Night Was Young* Kindle-vs-hardcover drift mode.

### G21. Markdown corruption signatures from round-tripping (§4.1)

Round-tripping through PDF or DOCX and back to text corrupts via embedded underscores, paragraph-not-terminated, unbalanced emphasis, etc. Run `lint_manuscript.py` before every build.

### G22. Don't combine pass dimensions (§4.2)

Each revision pass should target one axis. "Tighten this AND thread a motif" produces a passage that's both compressed and expanded with visible seams.

### G23. Wrong character ornament on spine (cross-project)

`\u2726` (✦) is preferred in *The Night Was Young* and *The Second Notebook*. Make sure the font supports it — `Segoe UI Symbol` is the fallback. If the font lacks the glyph, the spine renders a tofu box.

---

## 16. Successful patterns to repeat

### 16.1 The three-format pipeline (per book)

For each book, produce in this order:
1. **KDP paperback** — first because the interior format is the most strict
2. **KDP hardcover** — same interior file, different cover (more turn-in, wider spine)
3. **Mixam premium hardcover** — same content, looser margins for ~10% more pages, different cover spec
4. **Kindle ebook** — same content, no print conventions
5. **Digital PDF** — same content, covers prepended to body

Once the KDP paperback is locked, every subsequent format is a transform.

### 16.2 The generator/composite layer

Per book, three generators:
- `generate_<book>_kdp.js` — KDP paperback docx + JSZip mirror-margin injection
- `generate_<book>_kindle.js` — Kindle docx with H1 + TOC, no print conventions
- `composite_cover_<book>_kdp.py` — KDP paperback wrap PDF
- `composite_cover_<book>_kdp_hardcover.py` — KDP hardcover wrap PDF
- `composite_cover_<book>.py` — Mixam three-panel covers
- `build_digital_<book>.py` — digital PDF assembly

Per the convention used for all three books, these get copied and renamed from the most-recent prior book and adjusted for the new title, page count, source paths.

### 16.3 The CONTINUATION_PROMPT.md handoff

Write at ~80% context fill. Capture: current state, files-of-record, completed passes, pending passes, key character facts, regeneration commands. Hand off cold to next instance.

### 16.4 The M0 soul document pattern

Before draft 1, produce a 30-50K character soul document for each principal character. The convergence test (outside voice + inside voice describe the same person) determines whether the architecture holds. Errors caught at M0 cost minutes; errors caught at draft 5 cost weeks.

### 16.5 The voice spec as enforcement

Maintain `voice/bo-voice/SKILL.md` (or equivalent for the active voice register). Run mechanical greps before every build:
- Forbidden words (delve, nuanced, ...)
- Em-dash audit
- Bullet list audit
- Hedge-word audit
- Generic-LLM-phrase audit

### 16.6 The lint pre-flight

Always run `lint_manuscript.py` before generating. Zero findings or known false-positives only. Any hit = halt build, investigate.

### 16.7 The parallel-instance audit

For any load-bearing passage (the comprehension the book exists to reach), feed it cold to a second Claude instance with file paths and ask: structural audit, missing beat, sufficiency check.

### 16.8 The font choice — Cormorant Garamond + Georgia

| Use | Font |
|---|---|
| Cover title and spine | **Cormorant Garamond Light** (variable axis, set weight per use) |
| Interior body | **Georgia** 11pt or 12pt |
| Math | **Cambria Math** |
| Code spans | **Consolas** |
| Ornaments | **Segoe UI Symbol** |

This pairing works across all three books and produces a literary-fiction register. Substituting either kills the aesthetic.

### 16.9 The color palette (navy + cream + gold)

Established once, reused with adjustments per book. See §5.2.

### 16.10 The single-source-of-truth markdown

All formats read from the same `part[1-N]_revised_v<N>.md` files. No format has its own copy. The generators do the format-specific work.

---

## 17. Cross-project contradictions

### C1. KDP hardcover board addition: 0.302" or 0.348"?

- **Old** (`C:\Claude-Titanic\PRODUCTION_LESSONS_LEARNED.md`, written April 20, 2026):
  > `+ 0.302"` for the case boards
- **New** (`composite_cover_city_kdp_hardcover.py` and `composite_cover_second_notebook_kdp_hardcover.py`, written April 24, 2026):
  > `HARDCOVER_BOARD_ADD_IN = 0.348` — "KDP 2026 hardcover: board + endpapers add 0.348" to the paper-spine. (Empirically calibrated against KDP Print Previewer rejections on the Autotelic Disposition build — previous Titanic-era notes said 0.302.)"

**Resolution:** Use 0.348" as current. The PRODUCTION_LESSONS_LEARNED file is from April 20, 2026 and was superseded by empirical findings from later builds. If the Print Previewer rejects with a different expected spine, recalibrate.

### C2. KDP wrap dimensions: arithmetic vs. validator

For 186pp cream:
- Arithmetic: width 14.184" × height 10.416"
- KDP says: 14.183" × 10.417"

**Resolution:** Use the values KDP's Print Previewer prescribes (4-decimal precision). When in doubt, override the height to 10.417" — the validator is canonical.

### C3. Margin convention drift between books

- **The Night Was Young KDP** (`generate_book_kdp.js`):
  - Gutter 0.625", outside 0.5", top 0.5", bottom 0.625"
- **The Night Was Young Mixam** (`generate_book_v12.js`):
  - Gutter 0.875", outside 0.625", top 0.625", bottom 0.75"
- **The City and the Girl KDP** (`generate_city_kdp.js`):
  - Gutter 0.625", outside 0.5", top 0.5", bottom 0.625" (matches Night Was Young KDP)
- **The Second Notebook KDP** (`generate_second_notebook_kdp.js`):
  - Same as The City and the Girl

**Resolution:** The KDP margin set (`0.625/0.5/0.5/0.625`) is now the canonical KDP-paperback default across books. Mixam's looser set (`0.875/0.625/0.625/0.75`) is for the premium hardcover only. Do not mix.

### C4. Body font size: 11pt or 12pt?

- *The Night Was Young* (KDP): 12pt with 340 DXA line spacing
- *The City and the Girl* (KDP): 11pt with 320 DXA line spacing
- *The Second Notebook* (KDP): 11pt with 320 DXA line spacing

**Resolution:** This is a per-book aesthetic call, not a contradiction. Longer books may prefer 11pt to keep page count manageable; shorter or "weightier" prose may use 12pt for readability. Both pass KDP validation.

### C5. Final character ornament

- *The Night Was Young*: `\u2726` (✦)
- *The City and the Girl*: `\u2726` (✦) with `\u00B7  \u00B7  \u00B7` (· · ·) section breaks
- *The Second Notebook*: same as City

**Resolution:** Use `\u2726` for major (Part-opening, spine) ornaments and `\u00B7  \u00B7  \u00B7` for within-chapter scene breaks.

### C6. Where is the production-lessons file kept?

There were two `PRODUCTION_LESSONS_LEARNED.md` files:
- `C:\Claude-Titanic\PRODUCTION_LESSONS_LEARNED.md` (April 20, 2026) — Titanic-era, partially superseded
- THIS file at `C:\ASTRA-7\book\production_lessons_learned.md` (May 15, 2026) — current canonical, supersedes the prior

**Resolution:** Read this file for current canon. The old file remains for historical reference.

---

## 18. Reference: tested script inventory

All scripts live at `C:\Claude-Titanic\` root unless noted. Copy and rename for the next book.

### 18.1 docx generators (Node)

| Script | Purpose |
|---|---|
| `generate_book_v12.js` | MD → Mixam docx (looser margins, 6×9, ~204pp at 12pt) — *Night Was Young* |
| `generate_book_kdp.js` | MD → KDP paperback docx (tighter margins, 12pt) — *Night Was Young* |
| `generate_kindle.js` | MD → Kindle docx (H1, TOC, no print conventions) — *Night Was Young* |
| `generate_city_kdp.js` | MD → KDP paperback docx (11pt, 3 Parts) — *The City and the Girl* |
| `generate_city_kindle.js` | MD → Kindle docx — *The City and the Girl* |
| `generate_second_notebook_kdp.js` | MD → KDP paperback docx — *The Second Notebook* |
| `generate_second_notebook_kindle.js` | MD → Kindle docx — *The Second Notebook* |

### 18.2 Cover composers (Python)

| Script | Purpose |
|---|---|
| `composite_cover.py` | Front-only title overlay on a single image (used for *City* front cover) |
| `composite_cover_titanic.py` | Mixam 3-panel cover (front + spine + back PDFs) — *Night Was Young* |
| `composite_cover_kdp.py` | KDP paperback single-wrap cover — *Night Was Young* |
| `composite_cover_kdp_hardcover.py` | KDP hardcover single-wrap cover (0.708" wrap, +0.302" board — old calibration) — *Night Was Young* |
| `composite_cover_city_kdp.py` | KDP paperback wrap — *The City and the Girl* |
| `composite_cover_city_kdp_hardcover.py` | KDP hardcover wrap (uses +0.348" board) — *The City and the Girl* |
| `composite_cover_second_notebook.py` | Mixam variant — *The Second Notebook* |
| `composite_cover_second_notebook_kdp.py` | KDP paperback wrap — *The Second Notebook* |
| `composite_cover_second_notebook_kdp_hardcover.py` | KDP hardcover wrap — *The Second Notebook* |

### 18.3 Digital PDF assemblers (Python)

| Script | Purpose |
|---|---|
| `build_digital_pdf.py` | Original — docx→PDF + Mixam covers → digital — *Night Was Young* |
| `build_digital_city.py` | Strips front matter, crops covers — *The City and the Girl* |
| `build_digital_second_notebook.py` | Same pattern — *The Second Notebook* |

### 18.4 Utility scripts

| Script | Purpose |
|---|---|
| `check_part_pages.py` | Word COM page-position verifier (recto/verso check) |
| `lint_manuscript.py` | Markdown corruption-signature linter |
| `strip_blank_pages.py` / `strip_blank_pages_v2.py` | Strip accidentally inserted blank pages from generated docx |

### 18.5 Dependencies

```
npm: docx (>= 9), jszip
python:
  PIL (Pillow) — image composition
  PyMuPDF (fitz) — PDF MediaBox precision
  PyPDF2 — PDF concatenation
  win32com.client (Windows + Word installed) — docx→PDF
  python-docx — word count parity check
```

---

## 19. Reference: exact-numbers cheat sheet

**Commit to muscle memory.** They are different for each service and format; one wrong number means a rejected upload.

### 19.1 Trim sizes used

- 6.00" × 9.00" — all three books, all formats

### 19.2 Bleed / wrap

- **Mixam cover:** 0.80" bleed on all four sides
- **Mixam interior:** 0.125" bleed
- **KDP paperback (cover or interior):** 0.125" bleed
- **KDP hardcover:** 0.708" wrap on all four sides

### 19.3 Spine width

- **Cream paper:** `SPINE_IN = PAGES × 0.0025`
- **White paper:** `SPINE_IN = PAGES × 0.002252`
- **KDP hardcover adds:** `+ 0.348"` (current; was `+ 0.302"` in old notes)
- **Mixam hardcover:** Mixam gives you the spine number in their job spec

### 19.4 Final KDP wrap dimensions

- **KDP paperback** = `(6.00 × 2) + spine + (0.125 × 2)` wide × `9.00 + (0.125 × 2)` tall
  - e.g. 186pp cream → 12.715" × 9.250", spine 0.465"
- **KDP hardcover** = `(6.00 × 2) + spine_with_boards + (0.708 × 2)` wide × `10.417"` tall
  - e.g. 186pp cream → 14.183" × 10.417", spine 0.813" (using 0.348 board) or 0.767" (using 0.302 board)

### 19.5 Page count multiples

- **Mixam:** must be multiple of 4
- **KDP:** must be multiple of 2

### 19.6 Margins

| Format | Top | Bottom | Gutter | Outside |
|---|---|---|---|---|
| **KDP paperback (11-12pt)** | 0.5" | 0.625" | 0.625" | 0.5" |
| **Mixam premium hardcover (12pt)** | 0.625" | 0.75" | 0.875" | 0.625" |

### 19.7 Body typography

| Format | Font | Size | Line spacing | First-line indent |
|---|---|---|---|---|
| KDP paperback | Georgia 11pt | 320 DXA | 360 DXA | Justified |
| KDP paperback alt | Georgia 12pt | 340 DXA | 360 DXA | Justified |
| Mixam | Georgia 12pt | 340 DXA | 360 DXA | Justified |
| Kindle | Georgia 12pt | 340 DXA | 360 DXA | Default (reader override) |

### 19.8 Cover typography

- Font: **Cormorant Garamond Light** (variable axis, weight 300-700)
- Title size: ~7.5% of image height (= `int(WRAP_H * 0.075)`)
- Title weight: 400-500
- Spine title weight: 700, double-drawn with 1px offset
- Tracking: 0.04-0.08 em
- Author byline: ~3.5% of image height, weight 400, tracking 0.10-0.12

### 19.9 Color palette

- Navy: `#0D1B2A`
- Umber (alt): `#120E16` / `#100C12`
- Cream: `#F4EFE0` (Titanic) or `#F0EADC` (Second Notebook)
- Warm cream: `#E4DBC8`
- Dimmed cream: `#AAA094`
- Gold: `#C9A760`
- Body text: `#1A1A1A`

### 19.10 Quiet zones

Keep typography at least `bleed + 0.25"` from any edge:
- Mixam: 1.05" from edges
- KDP paperback: 0.375" from edges
- KDP hardcover: 0.958" from outer edge of wrap (0.375" inside trim + 0.708" wrap on outside)

### 19.11 ISBN barcode keep-out (KDP back cover)

- 2.25" × 1.50" at bottom-right of back-cover panel

### 19.12 DPI

- 300 DPI for all print artifacts
- All composites at DPI = 300

---

## End of document

This document is meant to be self-contained. A Claude instance or Bo reading this cold should have everything needed to reproduce the pipeline for *The Long Watch* (or any future book) without re-derivation.

**Compiled by:** Claude (Opus 4.7, 1M context), 2026-05-15
**Source scope:** All process-relevant files at `C:\Claude-Titanic\` and its subdirectories
**Successor:** Update this file as *The Long Watch* production introduces new lessons. Mark provisional new findings as `(provisional, calibrated against The Long Watch only)`. Reconcile contradictions in §17 as they arise.
