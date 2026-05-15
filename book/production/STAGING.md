# Production Staging — Ready for Upload (DO NOT UPLOAD YET)

*Updated 2026-05-15 after all critical fixes applied.*

**Status:** ARTIFACTS READY · NOT YET UPLOADED.

This file lists every deliverable, its target upload destination, and the manual steps to publish. **Do not actually upload until Bo gives explicit go.**

---

## Title (canonical, applied everywhere)

**`ASTRA-7: The Long Watch`**

## License

**`CC BY-SA 4.0`** for the book (this work).

License files in repository:
- `C:\ASTRA-7\LICENSE` — MIT (simulator code, separate)
- `C:\ASTRA-7\book\LICENSE` — **CC BY-SA 4.0 (book)** ← prominent

License also stated in:
- `book/manuscript/front_03_copyright.md` (interior copyright page)
- `book/manuscript/back_02_colophon.md` (back matter)

## Project URLs (verified from `memory/resources_external.md`)

- **Website:** https://astra-7.com (Cloudflare-hosted, static)
- **GitHub:** https://github.com/bochen2029-pixel/astra-7
- **Hugging Face:** https://huggingface.co/bochen2079/ASTRA-7
- **Steam:** Coming Soon page TBD

---

## Deliverables

### 1. Kindle ebook (KDP digital)

**Target:** kdp.amazon.com → Create New Kindle eBook

**Artifacts:**
- `outputs/kindle/The_Long_Watch_KINDLE.docx` — interior, TOC populated, 124 KB, 45,713 words
- `outputs/kindle/The_Long_Watch_KINDLE_cover.jpg` — front cover, 1600×2560, 54 KB

**Upload steps:**
1. Sign in to kdp.amazon.com
2. Create New Kindle eBook
3. **Title:** `ASTRA-7: The Long Watch`
4. **Subtitle:** (leave blank)
5. **Author:** `Bo Chen`
6. **Description:** paste from `book/back_cover.md`
7. **Keywords:** (manual, e.g.: AI, starship, single-player, autotelic, literary fiction, science fiction, open source)
8. **Categories:** Literary Fiction, Science Fiction, Philosophy of Mind
9. Upload `The_Long_Watch_KINDLE.docx` for interior
10. Upload `The_Long_Watch_KINDLE_cover.jpg` for cover
11. **Pricing:** $0.00 to $4.99 (Bo's call; KU/Select declined per prior decisions)
12. **DRM:** OFF (project ethos)
13. Submit for review (~72 hr typical)

---

### 2. KDP Hardcover

**Target:** kdp.amazon.com → Add Hardcover format

**Artifacts:**
- `outputs/kdp_print/The_Long_Watch_PRINT_INTERIOR.docx` — interior, 131 KB
- `outputs/kdp_print/The_Long_Watch_PRINT_INTERIOR.pdf` — PDF version
- `outputs/kdp_print/cover_wrap_hardcover.pdf` — cover wrap, 524 KB
- `outputs/kdp_print/cover_wrap_hardcover.jpg` — preview

**Specs:**
- Trim: 6 × 9 inches
- **Pages: 186** (even, KDP-compliant)
- Words: 45,717
- Cover wrap: 14.122 × 10.417 inches
- **Spine width: 0.706"** (pages × 0.0025 + 0.241, empirical post-IIR v3 formula)
- Paper: WHITE (cream not available for KDP hardcover)
- Mirror margins applied, recto enforcement, page numbers, running header

**Upload steps:**
1. From the Kindle listing → Add Hardcover format (links by ASIN)
2. Or create new Hardcover listing
3. Title, Author, Description: SAME as Kindle
4. Categories: SAME
5. **Interior:** upload `The_Long_Watch_PRINT_INTERIOR.docx`
6. **Cover:** upload `cover_wrap_hardcover.pdf`
7. Paper: WHITE (only option)
8. **Run Print Previewer**. If rejected:
   - Note KDP's stated expected dimensions
   - Update `PAGES` and/or spine formula in `composite_cover_kdp_hardcover.py`
   - Regenerate cover
   - Re-upload
   - Iterate until accepted
9. Pricing: $24.99-29.99 typical hardcover
10. Submit for review

---

### 3. KDP Paperback

**Target:** kdp.amazon.com → Add Paperback format

**Artifacts (NOT YET BUILT):**
- Same interior as hardcover (`The_Long_Watch_PRINT_INTERIOR.docx`)
- Paperback cover wrap (need to run `composite_cover_kdp_paperback.py`)

**Specs:**
- Trim: 6 × 9 inches
- Pages: 186 (same as hardcover)
- Cover wrap: 12.669 × 9.250 inches
- **Spine width: 0.419"** (pages × 0.002252, no board offset)
- Bleed: 0.125" all sides

**To build cover:** `python composite_cover_kdp_paperback.py` (PAGES already at 200 placeholder; update to 186 before running)

---

### 4. Digital PDF

**Target:** distribute via GitHub releases, website, Hugging Face (separate from Kindle)

**Artifacts (NOT YET BUILT):**
- `outputs/digital/The_Long_Watch_DIGITAL.pdf` (will be built from print interior PDF + Kindle cover prepended)

**To build:** `python build_digital_with_covers.py`

---

### 5. Mixam Premium Hardcover (optional, not yet scripted)

Bo mentioned Mixam is okay. Reference scripts in `_reference_inside_the_region/`:
- `composite_cover_mixam.py`
- `build_mixam_interior.py`

These can be adapted later for the premium hardcover edition. Not part of this round.

---

## What is NOT done yet

- [ ] **Cover real artwork** — current covers are minimal ASTRA-7 wordmark style; if you want hull imagery on front, that needs to be designed/generated separately. Current minimal design matches Bo's explicit screenshot directive.
- [ ] **KDP upload** — all artifacts ready; explicit go from Bo required
- [ ] **GitHub release for digital PDF** — not pushed
- [ ] **Hugging Face release** — not pushed
- [ ] **Paperback build** — script ready, page count is 186, just needs running
- [ ] **Digital PDF build** — same

---

## Fixes applied in this round (TODO.md items)

1. ✅ **Title is now `ASTRA-7: The Long Watch` everywhere** (generators, manuscript, spine, etc.)
2. ✅ **Front matter content pushed down on each page** (empty-paragraph spacers; PUSHDOWN map per file type)
3. ✅ **Colophon double-H1 bug fixed** (no longer emits filename-based title; file's own `# Title` is the single H1)
4. ✅ **Trailing blank page defensively fixed** (now uses `new Paragraph({})` with no TextRun; should reduce "text outside margins" rejections)
5. ✅ **CC BY-SA 4.0 license stated** in three places: `book/LICENSE`, copyright page, colophon
6. ✅ **Real URLs** baked in (replaced `[your-handle]` placeholders)
7. ✅ **Staging documented** (this file)
8. ✅ **Downstream hardcover regenerated** with all the above

---

## How to verify

1. Open `outputs/kindle/The_Long_Watch_KINDLE.docx` in Word/Calibre/Kindle Previewer:
   - Title appears as "ASTRA-7: The Long Watch"
   - Front matter pages render with content centered (not at top)
   - Colophon appears once, not twice
2. Open `outputs/kdp_print/The_Long_Watch_PRINT_INTERIOR.pdf`:
   - Title page shows "ASTRA-7: The Long Watch"
   - Half-title, title page, copyright, epigraph all centered on their pages (not at top)
   - Each cycle starts on a right-hand (recto) page
   - Page numbers in footer
   - Running header "ASTRA-7: THE LONG WATCH"
   - Colophon appears once
3. Open `outputs/kdp_print/cover_wrap_hardcover.jpg`:
   - Front: ASTRA-7 wordmark + hex (matches Kindle)
   - Spine: "ASTRA-7: THE LONG WATCH" vertical
   - Back: description text in white on navy, well-positioned

If anything is wrong, regenerate via the pipeline:
```
node generate_kindle.js
python update_kindle_toc.py
node generate_book_kdp_hardcover.js
python update_hardcover_and_count.py
python composite_cover_kindle.py
python composite_cover_kdp_hardcover.py
```
