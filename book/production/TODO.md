# Production fix TODO

*Created 2026-05-15. From Bo's feedback on first Kindle build.*

## Issue 1: Title is wrong

**Status:** TODO

**Required:** Full title is **`ASTRA-7: The Long Watch`** — applied to:
- KDP listing metadata (manual at upload time)
- Half-title page
- Title page
- Running header
- Spine of hardcover/paperback
- Front matter source files
- Generator constants in both `.js` generators
- Cover composite scripts (where title appears)
- SPECS.md

Inside the prose, "The Long Watch" alone is still appropriate ("*The Long Watch* is a single-POV literary novel..." in back cover, etc.). The official title is the longer form.

## Issue 2: First 2-3 pages content too high

**Status:** TODO

**Root cause:** `spacing.before` on a paragraph immediately after a `PageBreak` is unreliable in Word. The half-title, title page, copyright, and epigraph render at the top of the page instead of centered.

**Fix:** Replace `spacing.before` with explicit empty-paragraph spacers to push content down to the desired vertical position on each front-matter page.

**Lessons-learned reference:** Inside_The_Region used hardcoded `spacing.before` values that worked because the FIRST paragraph of a section honors `before`. But subsequent pages within the same section after `PageBreak` don't. Fix is empty-paragraph spacers, not `before` values.

## Issue 3: Colophon appearing TWICE

**Status:** TODO

**Root cause:** The generator's `BACK_MATTER_TITLES` map adds an H1 "Colophon" from filename. Then `parseMarkdown` parses the file's own `# Colophon` header into ANOTHER H1. Result: two H1 pages back-to-back (first empty, second with content).

**Fix:** Remove the title-from-filename insertion. Let each back-matter file own its own `# Title` H1. This also simplifies the back-matter handling logic.

**Side effect:** back-matter stub files need their own `# Title` line when filled in. Already true for `back_02_colophon.md`. Other stubs need this when they get filled.

## Issue 4: Last page out-of-margin rejections (recurring across books)

**Status:** TODO — preemptive fix

**Root cause:** The trailing `EVEN_PAGE` blank paragraph contains an empty `TextRun` with non-zero font size and a white color. KDP's preflight may detect this as "content out of margin" even though it's invisible.

**Fix:**
- Use `new Paragraph({})` (truly empty, no TextRun) for the trailing blank section's content
- Verify section margins are conservative enough for KDP's tolerance
- Verify XML inspection shows no inherited header/footer content in `header*.xml` / `footer*.xml` of the last section

**Lessons-learned reference:** Inside_The_Region addendum 7 documented the empty-headers/footers fix. This is ALSO needed, BUT additionally the paragraph content itself must be truly empty (not "empty TextRun with size:2 color:FFFFFF" — that's still a TextRun).

## Issue 5: License and URLs not in copyright

**Status:** TODO

**Required:**
- **License: CC BY-SA 4.0** (per Bo)
- **GitHub:** `https://github.com/bochen2029-pixel/astra-7`
- **Hugging Face:** `https://huggingface.co/bochen2079/ASTRA-7`
- **Website:** `https://astra-7.com`

These are pulled from `memory/resources_external.md`. Apply to:
- `front_03_copyright.md` (full license text + URLs)
- `back_02_colophon.md` (replace `[your-handle]` placeholders with actual URLs)

## Issue 6: License needs to be prominent and easily found

**Status:** TODO

**Required:** Bo wants the license info easily findable. Approach:
- Full license statement on copyright page (front_03)
- Also a `LICENSE` file at `C:\ASTRA-7\book\LICENSE` (or possibly at `C:\ASTRA-7\LICENSE` as the project root)
- Mention in colophon (back_02)
- Mention in book metadata (manual at KDP upload)

## Issue 7: Stage but don't upload yet

**Status:** TODO (operational discipline)

After regenerating everything, DO NOT:
- Run `git push`
- Upload to KDP
- Upload to Hugging Face
- Run any deployment commands

DO:
- Commit work to local git (probably OK)
- Have all artifacts ready in `outputs/`
- Have all docs in place
- Make explicit handoff to Bo for upload step

## Issue 8: Downstream hardcover same fixes

**Status:** TODO

All the above fixes apply to hardcover/paperback too:
- Title change → spine + running header + interior
- Front matter pushdown → applies to print interior
- Back matter double H1 → applies to print interior
- Last-page defensive fix → applies to print interior (it's the same generator)
- License + URLs → manuscript content same across formats

After fixes, regenerate:
1. Kindle DOCX (+ TOC update)
2. Print interior DOCX (+ TOC update + PDF + page count)
3. Hardcover cover wrap (with new title on spine)
4. Paperback cover wrap (when ready)
5. Digital PDF (rebuilds from print interior + cover)

---

## Execution order

1. Update memory/manuscript files (license, URLs, title)
2. Update generators (title constant, front matter pushdown, back matter H1 fix, trailing blank fix)
3. Update cover composites (title where appropriate)
4. Regenerate Kindle (DOCX + cover)
5. Regenerate Hardcover (interior + cover, requires page count from interior)
6. Regenerate Paperback cover
7. Regenerate Digital PDF
8. Verify outputs
9. Stage for upload (don't actually upload)
