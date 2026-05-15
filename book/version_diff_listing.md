# The Long Watch — Version Diff Listing

**Four publication versions (all 6.00" × 9.00" trim):**

1. **Kindle ebook** (KDP digital, reflowable)
2. **Digital PDF** (single-file, distributed via email / Google Drive, fixed-layout)
3. **Hardcover** (KDP case laminate)
4. **Paperback / softback** (KDP perfect-bound)

**Compiled:** 2026-05-15
**Authority:** `book/production_lessons_learned.md` (canonical, supersedes Amazon docs when in conflict per Bo's instruction) cross-referenced with empirical scripts at `C:\Claude-Titanic\` (the actually-shipped three-book corpus) and Amazon KDP documentation accessed May 2026.

When this document and the lessons-learned doc disagree, the lessons-learned doc wins.
When the lessons-learned doc and current Amazon docs disagree, the lessons-learned doc wins (per Bo's instruction; Amazon docs have known errors).
Both classes of conflict are flagged in §4.

---

## Table of Contents

1. [Quick-reference summary table](#1-quick-reference-summary-table)
2. Per-version deep-dive:
   - [2a. Kindle ebook (full spec)](#2a-kindle-ebook-full-spec)
   - [2b. Digital PDF (full spec)](#2b-digital-pdf-full-spec)
   - [2c. Hardcover, KDP case laminate (full spec)](#2c-hardcover-kdp-case-laminate-full-spec)
   - [2d. Paperback / softback, KDP perfect-bound (full spec)](#2d-paperback--softback-kdp-perfect-bound-full-spec)
3. Side-by-side diff tables:
   - [3a. Interior file specs](#3a-interior-file-specs-side-by-side)
   - [3b. Cover file specs](#3b-cover-file-specs-side-by-side)
   - [3c. Metadata specs](#3c-metadata-specs-side-by-side)
   - [3d. Distribution / channel specs](#3d-distribution--channel-specs-side-by-side)
   - [3e. Pricing / royalty specs](#3e-pricing--royalty-specs-side-by-side)
4. [CONFLICT FLAGS](#4-conflict-flags)
5. [OPEN DECISIONS (Bo needs to call)](#5-open-decisions-bo-needs-to-call)
6. [Sources cited](#6-sources-cited)

---

## 1. Quick-reference summary table

| Spec | Kindle | Digital PDF | Hardcover (KDP) | Paperback (KDP) |
|---|---|---|---|---|
| **Trim** | reflowable; 1.6:1 cover only | 6.00" × 9.00" fixed | 6.00" × 9.00" trim block | 6.00" × 9.00" trim block |
| **Interior file format** | DOCX (preferred), EPUB, KPF | PDF (PyMuPDF-built, single file) | PDF (Word COM-exported, fonts embedded) | PDF (Word COM-exported, fonts embedded) |
| **Cover deliverable** | Single JPEG/TIFF, front only, 1600×2560 px | Front + back as 2 PDF pages, 6×9 trim only | Single-wrap PDF: back + spine + front | Single-wrap PDF: back + spine + front |
| **Bleed / wrap** | N/A (no bleed) | N/A (no bleed; covers cropped to trim) | 0.708" case wrap on all 4 sides | 0.125" bleed on all 4 sides |
| **Spine** | N/A | N/A | `pages × 0.0025 + 0.348"` (cream) | `pages × 0.0025"` (cream) |
| **Color profile** | sRGB / RGB | sRGB (digital), embedded as-is | CMYK preferred, no profile recommended | CMYK preferred, no profile recommended |
| **DPI** | 300 recommended; 72 minimum | 300 (matches print source) | 300 minimum, 300 actual | 300 minimum, 300 actual |
| **Cover dims (e.g. 200pp cream)** | 1600×2560 px (front only) | 6×9 front + 6×9 back | 14.183" × 10.417" (cream-spine equivalent) | 12.75" × 9.25" |
| **Page count constraint** | irrelevant (reflowable) | matches source PDF | even multiple of 2, 75-550 hardcover | even multiple of 2, 24-828 paperback |
| **Margins (interior)** | 1" all sides (suggestion only; ignored) | inherited from print PDF | mirror margins; top 0.5" bot 0.625" gutter 0.625" out 0.5" | mirror margins; top 0.5" bot 0.625" gutter 0.625" out 0.5" |
| **Body font** | Georgia 11pt (suggestion; reader overrides) | Georgia 11pt (fixed) | Georgia 11pt (fixed) | Georgia 11pt (fixed) |
| **Header/footer** | none (forbidden) | none on covers; print headers preserved on body | running head + page numbers on outer footer | running head + page numbers on outer footer |
| **Page numbering** | none | print numbering preserved | Arabic on body, starts 1 at first body page; front matter unnumbered | same as hardcover |
| **ToC** | navigable, hyperlinked, auto-built from H1 | print ToC preserved (not hyperlinked) | print ToC, manual page-number entries | print ToC, manual page-number entries |
| **ISBN** | not required (uses ASIN) | none | required (free KDP or owned Bowker) | required (free KDP or owned Bowker) |
| **Barcode keep-out** | none | none | 2.25" × 1.50" bottom-right of back panel | 2.25" × 1.50" bottom-right of back panel |
| **Mirror margins** | forbidden | inherited from print source (transparent) | required; inject via JSZip `<w:mirrorMargins/>` | required; inject via JSZip `<w:mirrorMargins/>` |
| **Expanded Distribution** | n/a | n/a | NOT available (Amazon-only) | available (opt-in, +$, lower royalty) |
| **Royalty model** | 70% ($2.99-$9.99) or 35% (else) | n/a (distributed by Bo, not Amazon) | 60% of list − printing cost | 60% of list − printing cost |
| **Min list price** | $0.99 | n/a | varies by page count; floor ≥ $0.01 royalty | varies by page count; floor ≥ $0.01 royalty |
| **Max list price** | $200 | n/a | no posted ceiling; pragmatic ~$100 | no posted ceiling; pragmatic ~$100 |
| **Pre-order** | yes (up to 1 year) | n/a | NO | NO |
| **Updates push to existing buyers?** | no, must opt in | n/a (each download is current) | n/a (physical) | n/a (physical) |
| **Page-count multiple** | irrelevant | irrelevant | 2 | 2 |
| **Paper option** | n/a | n/a | white only per Amazon; cream per lessons-learned (CONFLICT, §4 C1) | cream (literary default) or white |
| **Cover output script** | (built in InDesign/manual or front-only PNG via PIL) | `build_digital_*.py` (PyMuPDF) | `composite_cover_*_kdp_hardcover.py` (PIL + PyMuPDF) | `composite_cover_*_kdp.py` (PIL + PyMuPDF) |
| **Interior generator** | `generate_*_kindle.js` (Node + docx@9) | print PDF + cropped covers (PyMuPDF) | `generate_*_kdp.js` (Node + docx@9 + JSZip) | `generate_*_kdp.js` (Node + docx@9 + JSZip) |
| **docx→PDF route** | n/a (docx is final) | n/a (PyMuPDF assembles directly from print PDF) | Word COM (`win32com.client`) | Word COM (`win32com.client`) |
| **Required transparency flattening** | N/A | N/A | yes | yes |
| **PDF/X compliance** | N/A | preferred but not required | not required; flat PDF accepted | not required; flat PDF accepted |
| **Embedded fonts** | n/a (reader-substituted) | required (matches print) | required | required |

---

## 2a. Kindle ebook (full spec)

### 2a.1 Interior file

| Spec | Value |
|---|---|
| **File format** | `.docx` (preferred; Word 2007+); also `.epub` v3 or `.kpf` (Kindle Create) |
| **Trim / page size** | irrelevant; Kindle reflows. Page count estimated by Amazon from word count |
| **Margins** | 1.0" all four sides (1440 DXA top/bottom/left/right) as a suggestion; **Kindle ignores margins and uses its own renderer**. Document them but do not depend on them |
| **Gutter** | 0 (forbidden — no print binding) |
| **Bleed** | 0 (forbidden) |
| **Mirror margins** | **FORBIDDEN.** Single-section docx, no `<w:mirrorMargins/>` injection (and no JSZip post-process step) |
| **Page numbering** | **FORBIDDEN.** No footer with `PageNumber.CURRENT` |
| **Running headers** | **FORBIDDEN.** No header definition on the section |
| **Header / footer config** | `header: 0, footer: 0, gutter: 0` in the page properties; no `Header` or `Footer` objects |
| **Body font** | Georgia 11pt (BODY_SIZE = 22 half-points). Suggestion only — readers may override at runtime |
| **Body line spacing** | 320 DXA (~1.4× at 11pt), `lineRule: "atLeast"` |
| **First-line indent** | 360 DXA (~0.25") |
| **Body color** | `#1A1A1A` (not pure black) |
| **Justification** | `AlignmentType.JUSTIFIED` (Kindle may flatten to left, that's fine) |
| **Chapter break** | `new Paragraph({ children: [new PageBreak()] })` — Amazon's ingester reads these as logical chapter boundaries for the table of contents and the "go to next chapter" navigation |
| **Chapter heading style** | `HeadingLevel.HEADING_1` — **load-bearing.** Amazon's auto-TOC ingester scans for H1 paragraphs and uses them to build the navigation panel. If H1 is not applied, the TOC is empty |
| **ToC** | `new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-1", stylesWithLevels: [new StyleLevel("Heading1", 1)] })`. Place near the front; Amazon links to it from the navigation panel |
| **ToC links** | LIVE / hyperlinked. Each entry is clickable; auto-resolves to the H1 it references |
| **ToC update field** | Document built with `features: { updateFields: true }` so the TOC fills on first open |
| **Section break (within chapter)** | Three middle dots `· · ·` (U+00B7 × 3, double-spaced) in Segoe UI Symbol, 9pt (size 18 half-points), color `#999999`, centered. Same glyph as print. NO ornament `\u2726` mixing |
| **Italic spans** | `*word*` → italic; parser splits on `(\*[^*]+\*)/g` |
| **Bold spans** | `**word**` → bold; parser must split bold BEFORE italics (`(\*\*[^*]+\*\*)/g` first) to avoid asterisk collision |
| **Code spans** | Backtick-delimited; rendered in `Consolas`, no italic processing. Parser must split on backticks FIRST to avoid asterisks inside code being read as italic delimiters (G12 in §15 of lessons-learned) |
| **Math characters** | Tag with `font: "Cambria Math"` explicitly. Without explicit font, Kindle substitutes and breaks the glyph |
| **Hyperlinks** | LIVE in Kindle. Reflow-friendly. Should resolve to either intra-document anchors or external URLs |
| **Blank pages / blank versos** | **FORBIDDEN.** A blank screen mid-story reads as a defect to the Kindle reader |
| **Forced rectos** | **FORBIDDEN.** Page-break-before is allowed only at chapter boundaries; otherwise the reflow handles it |
| **Front matter** | Lean. Recommended: Title page (optional), Copyright page (minimal), Dedication (optional), Epigraph (optional), ToC, Body. NO half-title (print convention). NO blank pages between |
| **Back matter** | About the Author (load-bearing for discoverability), Other Books by the Author (if any). Avoid colophon (print convention) |
| **Page count target** | **DO NOT MATCH PRINT.** The 18-page gap between an ebook and its hardcover is entirely print conventions; trying to pad the ebook to match is anti-pattern (G11 in lessons-learned §15) |
| **Content parity discipline** | Parity is on **body word count**, not page count. Sum text runs with `python-docx` to verify: `wc = sum(len(r.text.split()) for para in doc.paragraphs for r in para.runs)`. Kindle may be slightly HIGHER than print due to About-the-Author. If LOWER, some revision didn't make it across — check the markdown source version in BOTH generators (G13 in lessons-learned §15: source-version drift) |
| **Embedded fonts** | not embedded. Kindle uses its own font set; readers override |
| **Transparency flattening** | N/A |
| **DPI for embedded images** | 300 PPI recommended; 96 PPI minimum |
| **Image color profile** | sRGB |
| **Reflowable vs fixed layout** | **Reflowable** for novels (Bo's case). Fixed-layout is for picture books, comics, cookbooks |
| **Section structure** | ONE section. `sections: [{ properties: { page: { margin: ... } }, children: [...all of it...] }]` |
| **File size** | typically ~100-200 KB for a 50K-word novel as docx; the on-Kindle .azw3 ends up similar |

### 2a.2 Cover file (Kindle)

| Spec | Value |
|---|---|
| **Trim / dimensions** | **1600 × 2560 pixels** (width × height) ideal |
| **Aspect ratio** | **1.6:1** (height ÷ width = 1.6) — Amazon recommendation |
| **Minimum dimensions** | 1000 × 625 pixels (do not approach the minimum; the cover renders at every thumbnail size from 50px to full-screen) |
| **Maximum dimensions** | 10,000 × 10,000 pixels per side |
| **File format** | JPEG (`.jpeg` / `.jpg`) **or** TIFF (`.tif` / `.tiff`). JPEG quality ≥ 80 recommended |
| **Color profile** | RGB (sRGB). Save WITHOUT color separation (no embedded CMYK) |
| **DPI** | 300 PPI recommended; 72 PPI accepted minimum |
| **File size** | < 50 MB hard cap |
| **Bleed** | NONE. The cover is rendered against an Amazon-provided background; bleed is meaningless |
| **Spine** | NONE. Kindle cover is FRONT ONLY |
| **Back cover** | NONE. Kindle cover is FRONT ONLY |
| **ISBN barcode** | NONE on cover. ISBN is metadata-only |
| **Cover text contents** | Title, subtitle (if any), author. Optional: tagline, series mark, edition note |
| **Suggested border** | Add a 3-4 pixel medium-gray border if the cover background is white/light, so the cover doesn't blend into Amazon's white page background |
| **Embedded in book file?** | NO. Cover is uploaded separately during KDP setup |

### 2a.3 Metadata (Kindle)

| Spec | Value |
|---|---|
| **Title** | up to 200 characters; no HTML; no all-caps; emojis disallowed |
| **Subtitle** | optional; up to 200 characters; concatenated with title in some listings |
| **Author name** | first + last; pen name allowed. Use the same author name across all formats to link them on the Amazon page |
| **Contributors** | up to 9 additional contributors (editor, illustrator, translator) |
| **Series info** | optional; series name + sequence number. Only useful for multi-book continuity |
| **Description** | up to **4000 characters** including HTML tags. Allowed HTML: `<b>`, `<i>`, `<br>`, `<p>`, `<h4>-<h6>`, `<ul>/<ol>/<li>`, `<em>`, `<strong>` |
| **Keywords** | exactly **7 keyword fields**, each up to **50 characters**. Comma-separated within a field is allowed but Amazon de-duplicates. Use the full 7 |
| **Categories** | up to 3 categories selected via KDP's category browser (replaces the old 2-category + BISAC system as of recent years). Amazon maps to internal BISAC codes |
| **BISAC** | not directly chosen on KDP; Amazon derives from category selection |
| **Age range / audience** | Adult, Young Adult, Teen, Children. Children's books have separate KDP categories. For *The Long Watch*: Adult |
| **Reading age** | optional; appears on listing |
| **Language** | choose from Amazon's supported list. English = `en` |
| **ISBN** | NOT required for Kindle. Amazon assigns an **ASIN** automatically. ASIN is the Kindle-side identifier |
| **DRM** | toggle: DRM-enabled or DRM-free. Once set on first publish, **cannot be changed.** Bo's ASTRA-7 ethos suggests DRM-free (open distribution); but for Kindle specifically, DRM-enabled gives slightly better KU eligibility signal |
| **Pre-order** | yes; up to 1 year ahead. Final manuscript due 3 business days before launch date |
| **Publication date** | the date Amazon publishes; settable on submission |
| **Imprint** | optional publisher name (default is "Independently published") |
| **Adult content flag** | toggle; affects search ranking |
| **Public domain** | toggle; doesn't apply to *The Long Watch* |

### 2a.4 Distribution (Kindle)

| Channel | Notes |
|---|---|
| **Amazon Kindle Store** | default; global |
| **Kindle Unlimited (KU)** | requires 90-day exclusivity (KDP Select). Bo's open-source ethos suggests NOT opting into KDP Select |
| **Library lending (Amazon)** | included by default |
| **Translation rights** | not part of Kindle metadata; separate negotiation |

### 2a.5 Pricing (Kindle)

| Tier | Value |
|---|---|
| **Min list price (US)** | $0.99 |
| **Max list price (US)** | $200.00 |
| **70% royalty band** | $2.99 - $9.99 (US, UK, DE, FR, ES, IT, JP, BR, IN, MX, AU, NL, CA) |
| **35% royalty band** | $0.99 - $2.98 and $10.00 - $200.00 |
| **Delivery fee (70% only)** | **$0.15 per MB** of the on-Kindle file size. For a 200 KB file ≈ $0.03; for a 5 MB file ≈ $0.75. Subtracted before the 70% multiplier |
| **Currency** | Auto-converts to local marketplace currency unless explicit per-marketplace price set |
| **Free pricing** | only via KDP Select promo (5 free days per 90-day period). For permanent free, must price-match through a Smashwords/Apple distribution route — not part of this corpus |

### 2a.6 Kindle-specific gotchas

- Parser asymmetry: backticks must split BEFORE italics (G12)
- Math without explicit font → renders as substitute glyph (G15)
- Existing customers don't auto-update to revised editions; they opt in via "Manage Your Content and Devices" (G14)
- Page count is irrelevant; do not pad (G11)
- Cover blends into Amazon white background if no border (cosmetic gotcha)

---

## 2b. Digital PDF (full spec)

This is the **single-file PDF** Bo distributes via email / Google Drive / direct download. It is NOT submitted to any platform; it is the author-controlled "give-away" edition.

### 2b.1 Interior file

| Spec | Value |
|---|---|
| **File format** | single `.pdf` |
| **Trim / page size** | 6.00" × 9.00" (matches print interior trim; MediaBox is 432 × 648 pts) |
| **MediaBox precision** | exact to 4 decimal places via PyMuPDF (`page = pdf.new_page(width=TRIM_W_IN * 72, height=TRIM_H_IN * 72)`) |
| **Margins** | inherited from the source print PDF (mirror margins are present in the PDF as rendered; they don't affect reading on screen because no facing-page rendering happens). Effective body region: gutter 0.625" / outside 0.5" / top 0.5" / bottom 0.625" |
| **Gutter / mirror margins** | INHERITED from source. PDF has them baked but they're cosmetic in a single-pane reader |
| **Bleed** | 0 (covers are CROPPED back to trim before assembly; print bleed stripped) |
| **Body font** | Georgia 11pt, embedded (carries over from Word COM export) |
| **Line spacing** | 320 DXA (~1.4×) inherited |
| **First-line indent** | 0.25" inherited |
| **Justification** | Justified, inherited |
| **Body color** | `#1A1A1A` inherited |
| **Header / footer** | INHERITED from print. Running head and page numbers are present on body pages |
| **Page numbering** | INHERITED from print. Front-matter unnumbered, body starts at 1, Arabic numerals |
| **Section break style** | `· · ·` (same as print) |
| **Chapter break style** | page break + Part heading (same as print) |
| **Front matter (print)** | half-title, blank verso, title page, copyright, dedication, blank, epigraph, blank — full sequence in source |
| **Front matter (digital, stripped)** | Strip blank verso (p2), title page (p3), copyright (p4). **Keep** half-title (p1) as a quiet divider between the covers and the body. Pattern set by *The Autotelic Disposition* and re-used for *City* and *Second Notebook* (`build_digital_*.py` scripts) |
| **Stripped pages (1-indexed)** | `FRONT_MATTER_TO_STRIP_1IDX = {2, 3, 4}` per the build script. Additionally, all all-blank body pages auto-inserted by ODD_PAGE recto enforcement are stripped via `identify_blank_pages()` (text-empty + image-empty) |
| **Back matter** | typically preserved (About the Author, etc.) |
| **Hyperlinks** | LIVE (PDFs preserve hyperlinks). Useful if the body cites URLs |
| **ToC** | print ToC if present; NOT hyperlinked (the source print PDF doesn't have linked ToC entries) |
| **Embedded fonts** | required; carried over from Word COM export |
| **Transparency** | none (flat) |
| **Compression** | `out.save(str(OUT_PDF), deflate=True, garbage=4, clean=True)` via PyMuPDF |
| **File size** | typically **1-2 MB** for a 200-page novel with compression on |
| **DPI** | 300 (matches print source) |
| **Color profile** | sRGB (the print source uses CMYK; the digital PDF inherits whatever Word exported — typically sRGB after Word's PDF export) |

### 2b.2 Cover (Digital PDF)

The digital PDF prepends TWO cover pages before the body, each at 6×9 trim.

| Spec | Value |
|---|---|
| **Page 1 (front cover)** | 6.00" × 9.00", MediaBox set exactly via PyMuPDF |
| **Page 2 (back cover)** | 6.00" × 9.00", MediaBox set exactly |
| **Bleed** | STRIPPED. The print cover has 0.125" bleed (KDP) baked; the digital crop removes it: `cropped = img.crop((BLEED_PX, BLEED_PX, img.width - BLEED_PX, img.height - BLEED_PX))` where `BLEED_PX = int(0.125 * 300)` for KDP-source crops, or `int(0.80 * 300)` for Mixam-source crops |
| **Spine** | NOT INCLUDED. Digital is two pages, not a wrap |
| **Source for front** | `cover_final.png` (title baked, no author per the *The City and the Girl* convention; *The Night Was Young* convention had author on front) |
| **Source for back** | back panel cropped from the paperback wrap (`outputs/kdp_paperback/cover_wrap.jpg`) — the print blurb is preserved exactly. ISBN barcode IS present in the back-cover crop because it's part of the print panel; Bo can decide to mask it before crop if desired (OPEN-DECISION-3 below) |
| **Title text** | Cormorant Garamond Light, weight ~500, tracked 0.04-0.08 em, baked at PIL composite time |
| **Author text** | Cormorant Garamond Light, weight 400, tracked 0.10-0.12 em |
| **DPI** | 300 (matches `front_img.save(front_tmp, "JPEG", quality=92, dpi=(DPI, DPI))`) |
| **JPEG quality** | 92 for the cover-pages intermediate JPEGs |
| **File format on page** | the cover is JPG embedded inside the PDF page; the page itself is PDF |
| **Color profile** | sRGB |
| **ISBN barcode** | inherited from paperback back panel crop (it IS present unless Bo masks it pre-crop) |

### 2b.3 Metadata (Digital PDF)

Digital PDF carries no platform metadata. The metadata that survives:

- **PDF metadata fields** (Title, Author, Subject, Keywords, Creator, Producer) — settable via `pdf.set_metadata({...})` in PyMuPDF; not currently set by `build_digital_*.py` scripts. **OPEN-DECISION-4:** decide whether to set PDF metadata.
- **No keywords / categories / pricing / ISBN apply** (digital is direct distribution)
- **Watermark** — not used; if Bo wants tracking on per-recipient distribution, add a recipient watermark via PyMuPDF
- **DRM** — none (incompatible with Bo's open-source ethos)

### 2b.4 Distribution (Digital PDF)

| Channel | Notes |
|---|---|
| **Direct download** | Bo's website (TBD) |
| **Email** | direct send |
| **Google Drive / Dropbox** | direct link share |
| **Hugging Face** | `astra-7-bundle` repo could host as a companion artifact |
| **GitHub Releases** | could host as a release asset |
| **Library distribution** | none |
| **Pre-order** | n/a |
| **Returnability** | n/a (it's a give-away) |

### 2b.5 Pricing (Digital PDF)

| Tier | Value |
|---|---|
| **Listed price** | typically **free** for ASTRA-7-aligned distribution |
| **Royalty model** | n/a |
| **Currency** | n/a |

### 2b.6 Digital-PDF-specific gotchas

- The crop-bleed step uses **0.125"** for KDP-source covers and **0.80"** for Mixam-source covers. Wrong constant → cover has visible bleed bar or under-crops into typography (G8 in lessons-learned §15)
- The half-title page must be PRESERVED (p1); the blank verso, title page, copyright (p2, p3, p4) are stripped because the covers carry their content
- All-blank body pages auto-inserted by ODD_PAGE enforcement must be stripped via `identify_blank_pages()` (text-empty + image-empty)
- The back-cover image carries the printed ISBN barcode unless masked. Aesthetically defensible (book authenticity) but Bo may prefer to strip it for digital — see OPEN-DECISION-3

---

## 2c. Hardcover, KDP case laminate (full spec)

KDP's hardcover is **case laminate**: the printed image is laminated directly onto the cardboard case. No dust jacket. The cover artwork wraps around two rigid boards (front and back) joined by a spine board.

### 2c.1 Interior file

| Spec | Value |
|---|---|
| **File format** | `.pdf` (preferred) or `.docx`. Always submit PDF for control. Generated via Word COM (`win32com.client.Dispatch("Word.Application")`, `doc.SaveAs(..., FileFormat=17)`) |
| **Trim / page size** | **6.00" × 9.00"** trim block. The HARDCOVER trim is the same as the paperback — the cover wraps boards that are taller/wider than the trim, but the interior pages are 6×9 |
| **Top margin** | 0.5" (720 DXA) |
| **Bottom margin** | 0.625" (900 DXA) |
| **Inside / gutter margin** | 0.625" (900 DXA). **Exceeds KDP minimum** (0.375" for ≤150pp, 0.5" for 151-300pp) — Bo's aesthetic choice for breathing room |
| **Outside margin** | 0.5" (720 DXA) |
| **Header inset** | 0 |
| **Footer inset** | 360 DXA (~0.25") below the bottom margin |
| **Mirror margins** | **REQUIRED.** `mirror: true` in the section page properties. THEN inject `<w:mirrorMargins/>` into `word/settings.xml` via JSZip post-process. Without injection, `docx@9` silently drops the flag and the print has constant gutter (text crawls into the spine on alternate pages). (G16 in lessons-learned §15) |
| **Bleed (interior)** | 0.125" if any element bleeds; otherwise no bleed required. Bo's design has no full-bleed interior elements, so the body interior is trim-only |
| **Body font** | Georgia 11pt (BODY_SIZE = 22 half-points) |
| **Body line spacing** | 320 DXA (~1.4×), `lineRule: "atLeast"` |
| **First-line indent** | 360 DXA (~0.25") |
| **Body color** | `#1A1A1A` |
| **Justification** | `AlignmentType.JUSTIFIED` |
| **Running header** | centered, 7.5pt Georgia (size 15 half-points), color `#AAAAAA`, characterSpacing 30. Text: book title in all caps (e.g., "THE LONG WATCH"). NO header on front matter; the convention varies on Part-opening pages — *The Night Was Young* uses continuous header |
| **Footer** | mirror-aligned page numbers: RIGHT-aligned on recto (default footer), LEFT-aligned on verso (even footer). 9pt Georgia (size 18 half-points), color `#888888`. Implementation: `footers: { default: new Footer({ ... AlignmentType.RIGHT ...}), even: new Footer({ ... AlignmentType.LEFT ...}) }` |
| **Page numbering scheme** | front matter UNNUMBERED. Body restarts at 1: `pageNumbers: { start: 1 }` on the body section. Arabic numerals (`PageNumber.CURRENT`) |
| **Section break ornament** | three middle dots `· · ·` (U+00B7 × 3, double-spaced), Segoe UI Symbol, 9pt, color `#999999`, centered. Spacing before/after: 240 DXA |
| **Chapter / Part break ornament** | `\u2726` (✦) — black four-pointed star, Segoe UI Symbol, 11pt (size 22 half-points), color `#999999`, centered. Placed beneath the heading |
| **Part heading** | centered, 13pt Georgia (size 26 half-points), all-caps, characterSpacing 60 or 80, `HeadingLevel.HEADING_1`, with `\u2726` ornament beneath. Spacing before: 2400 DXA (~1.67"); after: 500 DXA |
| **Part page break behavior** | each Part starts on a recto (odd page) via `SectionType.ODD_PAGE`. If a Part would land on verso, an automatic blank verso is inserted before it |
| **Drop caps** | NOT used in any of the three prior books. Optional for *The Long Watch* (OPEN-DECISION-5) |
| **ToC** | print ToC, manually generated. Page numbers entered by hand AFTER `check_part_pages.py` runs and reports recto/verso for each Part. NOT hyperlinked (print only) |
| **Front matter pages (canonical hardcover sequence)** | Page 3 (recto) Half-title; Page 4 (verso) Blank; Page 5 (recto) Full title page; Page 6 (verso) Copyright at bottom of page (traditional); Page 7 (recto) Dedication; Page 8 (verso) Blank; Page 9 (recto) Epigraph; Page 10 (verso) Blank; Page 11 (recto) Part I begins. Pages 1-2 are cover (Mixam/KDP handles separately) |
| **Back matter** | for hardcover: often omitted or minimal. Author bio optional |
| **Image specs (if any embedded)** | 300 DPI minimum; embedded (not linked); CMYK color profile preferred (but KDP recommends no embedded profile); transparency flattened |
| **Hyperlinks (live)** | discouraged in print body (cannot be clicked). For URLs in body, footnote/parenthesize the URL as plain text |
| **Embedded fonts** | REQUIRED. Word COM export embeds by default |
| **Transparency flattening** | REQUIRED. Use Word's "Save As PDF" with "ISO 19005-1 compliant (PDF/A)" off, but ensure no transparency layers — Word COM at `FileFormat=17` (wdFormatPDF) flattens by default |
| **PDF/X** | NOT required by KDP. Plain PDF accepted. PDF/X-1a is the printer-traditional standard but unnecessary |
| **Spot colors** | NOT supported; if used, must convert to CMYK process |
| **Page count constraints** | **75 pages minimum for hardcover** (KDP rule). **550 pages maximum.** Bo's *The Long Watch* is targeting ~200pp so well within bounds |
| **Page count multiple** | **2** (even number) |
| **Page count parity check** | run `check_part_pages.py` (Word COM) before submitting; it reports recto/verso for each Part heading. If a Part is on verso, insert a blank verso before it via an extra `EVEN_PAGE` section break |
| **Trailing blank gotcha** | if the final page lands on EVEN_PAGE (verso), the empty paragraph cursor must be **center-aligned** and **footers explicitly emptied**, otherwise KDP's margin validator flags "text outside the margins" on the cursor position. Use the explicit empty-trailing-section pattern from `generate_*_kdp.js` (G17 in lessons-learned §15) |
| **docx → PDF route** | Word COM (`win32com.client.Dispatch("Word.Application")` → `doc.SaveAs(path, FileFormat=17)`). NOT Pandoc, LibreOffice headless, or docx2pdf-cloud — all produce bad PDFs with font substitution, broken TOC, mis-paginated headers (G4 in lessons-learned §15) |

### 2c.2 Cover file (KDP hardcover, case laminate)

| Spec | Value |
|---|---|
| **Cover file format** | single-wrap PDF (back + spine + front in one file, left-to-right) |
| **Color profile** | CMYK preferred. **KDP explicitly recommends not embedding a color profile** at all (let the printer handle); spot colors must be converted to CMYK process |
| **DPI** | 300 |
| **Wrap (turn-in)** | **0.708" on all four outer edges** per lessons-learned (calibrated against KDP Print Previewer empirically on the Autotelic Disposition build). NOT 0.125" bleed (that's paperback). CONFLICT: Amazon docs and kdpcoverlab.com say 0.625" or 0.591" — see §4 C2. **Use 0.708" per Bo's instruction** |
| **Spine width** | `paperback_spine + 0.348"` where `paperback_spine = pages × 0.0025` (cream) or `pages × 0.002252` (white). The 0.348" is the empirically-calibrated case-board + endpapers addition. CONFLICT: old Titanic-era note said 0.302"; web shows 0.06"; see §4 C3 |
| **Wrap width formula** | `WRAP_W_IN = 0.708 + 6.00 + spine_w + 6.00 + 0.708` |
| **Wrap height formula** | KDP **uses 10.417"** exactly (not the arithmetic 9.00 + 0.708×2 = 10.416). Override to 10.417 to pass the 4-decimal validator (G18 in lessons-learned §15) |
| **Worked example, 200pp cream** | paperback spine 0.500"; hardcover spine 0.848"; wrap 14.264" × 10.417" |
| **Worked example, 100pp cream** | paperback spine 0.250"; hardcover spine 0.598"; wrap 14.014" × 10.417" |
| **Worked example, 186pp cream** | paperback spine 0.465"; hardcover spine 0.813"; wrap 14.183" × 10.417" (THIS IS THE KDP-VALIDATOR-CONFIRMED VALUE for *The Night Was Young*-era 186pp build) |
| **PDF MediaBox precision** | exact to 4 decimal places via PyMuPDF (`page = pdf.new_page(width=WRAP_W_IN * 72, height=WRAP_H_IN * 72)`). PIL's `img.save(..., "PDF", resolution=DPI)` is imprecise by ~1/1000" and fails KDP's validator (G19 in lessons-learned §15) |
| **Maximum file size** | 650 MB; recommended ≤ 40 MB |
| **Quiet zone (typography keep-out from outer edge)** | wrap + 0.25" = **0.958"** from outer edge (i.e., 0.375" inside the trim, plus the 0.708" wrap that folds around the boards). Spine-side: even wider, padded 0.5" inside the spine boundary to allow for hinge channel |
| **Front cover content** | title, subtitle (optional), author name. Cormorant Garamond Light. Title size = `int(WRAP_H * 0.075)` ≈ 234px at 300 DPI; weight 400-500; tracking 0.04-0.08 em |
| **Back cover content** | tagline (4 short lines, all-caps, gold `#C9A760`, tracked 0.06-0.08 em), pull-quote (italic, warm cream `#E4DBC8`, ~7-9pt), blurb body (150-200 words, cream `#F4EFE0` or `#F0EADC`, ~6pt), closing byline (e.g., "— a novel by Bo Chen", dimmed cream `#AAA094`) |
| **Back cover image treatment** | same AI-art image as front, but darkened to ~75-82% black (alpha 184-210 in RGBA overlay) before drawing the typography |
| **Spine content** | title (rotated -90°, top-to-bottom read), ornament (`\u2726`), author. ALL in CREAM on UMBER/NAVY ground. Weight 600-700, double-drawn 1px offset for visual bold; tracking 0.04 em |
| **Spine text minimum** | KDP requires AT LEAST 79 pages for spine text. Below 79pp, no spine text allowed. *The Long Watch* exceeds this comfortably |
| **Spine text safe zone (within spine width)** | 0.0625" margin on each side of spine. So usable spine-text area = `spine_width - 0.125"` |
| **ISBN placement** | back cover, bottom-right. KDP auto-generates the EAN-13 barcode for the assigned/owned ISBN and places it on the cover at print time IF the cover has the keep-out zone clear |
| **ISBN barcode keep-out** | reserve **2.25" × 1.50"** at bottom-right of back cover panel. Blurb wraps adaptively (narrower text width when y-cursor descends past `barcode_top_y`) — see `composite_cover_*_kdp_hardcover.py` for the implementation pattern |
| **Author bio / photo placement** | NOT on hardcover cover (no flap for case laminate, since no dust jacket). Bio goes in interior back matter |
| **Imprint logo** | optional bottom-of-spine or back cover. Not present on prior three Bo books |
| **Dust jacket** | NOT available for KDP hardcover. Mixam supports DJ; KDP does not |
| **Endpapers** | KDP hardcover endpapers are stock white. Custom-printed endpapers NOT supported by KDP (Mixam yes) |
| **Head/tail bands** | NOT available for KDP hardcover (Mixam yes) |
| **Bookmark ribbon** | NOT available for KDP hardcover (Mixam yes) |
| **Lamination** | KDP uses gloss laminate by default; matte laminate is selectable as a print option at the SKU level — confirm at submission |
| **Paper option** | Per Amazon docs: WHITE ONLY for hardcover (no cream available). Per lessons-learned: cream is used (see CONFLICT §4 C1). **Resolution per Bo's instruction: try cream, validate via KDP Print Previewer; if rejected, switch to white** |

### 2c.3 Metadata (Hardcover)

Mostly mirrors paperback. Differences:

| Spec | Value |
|---|---|
| **ISBN** | REQUIRED. Separate ISBN from paperback and Kindle. Free KDP ISBN OR owned Bowker ISBN. **Each format gets its own ISBN.** Free KDP ISBN belongs to Amazon (technically) and limits cross-distributor portability |
| **Imprint** | tied to the ISBN. KDP free ISBN forces "Independently published" as imprint. Owned ISBN allows custom imprint |
| **Description** | same Amazon listing (paperback + hardcover share a single product page). Description is set once per format-bundle |
| **Keywords** | same 7 keywords across formats (shared on the bundled listing) |
| **Categories** | same up to 3 categories across formats |
| **Series info** | same |
| **Audience** | same (Adult) |
| **Pre-order** | **NOT AVAILABLE** for hardcover. Only Kindle supports pre-order |
| **Publication date** | settable on submission; goes live within 72 hours of approval |
| **Returnability** | KDP hardcover IS returnable (Amazon's standard policy); paperback has the option to enable Expanded Distribution returns (separate setting; Bo's prior books didn't enable) |

### 2c.4 Distribution (Hardcover)

| Channel | Available? | Notes |
|---|---|---|
| **Amazon (US, UK, DE, FR, ES, IT, JP, BR, MX, AU, NL, CA, IN)** | yes | global marketplace |
| **Expanded Distribution (Ingram et al, libraries, bookstores)** | **NO** | KDP hardcover is **NOT eligible for Expanded Distribution**. Hardcover via Ingram requires IngramSpark, separate setup |
| **Library lending** | n/a (physical) | books appear in Amazon's listings; libraries can purchase via Amazon Business |
| **Returnable** | yes | Amazon's standard return policy |

### 2c.5 Pricing (Hardcover)

| Tier | Value |
|---|---|
| **Royalty rate** | 60% of list price minus printing cost |
| **Print cost (US, black ink, 6×9 hardcover regular trim)** | 75-108pp: $6.80 fixed only (no per-page). 110-550pp: $5.65 fixed + $0.012 per page |
| **Print cost example (186pp B&W)** | $5.65 + (186 × $0.012) = $5.65 + $2.232 = **$7.88** |
| **Print cost example (200pp B&W)** | $5.65 + (200 × $0.012) = **$8.05** |
| **Min list price (US)** | calculated to give ≥ $0.01 royalty per sale. For 200pp B&W: minimum ≈ $13.42 (= $8.05 / 0.6 + epsilon). Use KDP's automatic minimum at submission |
| **Max list price (US)** | no posted ceiling; pragmatic ~$100 |
| **Royalty example (200pp, $24.99)** | $24.99 × 0.6 − $8.05 = $14.994 − $8.05 = **$6.94 per sale** |
| **Currency** | per-marketplace auto-conversion; or override per-marketplace |
| **Print cost (premium color)** | $5.65 fixed + $0.065 per page (75-550pp). 200pp color: $18.65 print cost |

### 2c.6 Hardcover-specific gotchas

- The 0.708" wrap vs 0.625" / 0.591" / 0.394" Amazon-doc inconsistency: lessons-learned wins (§4 C2). The 0.708" value is empirically validated via the *The Night Was Young* and *The Autotelic Disposition* submissions
- 0.348" board addition vs old 0.302" note: use 0.348" (§4 C3)
- Height = 10.417" not 10.416" (G18)
- KDP hardcover NOT in Expanded Distribution
- KDP hardcover NO pre-order
- KDP hardcover NO dust jacket
- KDP hardcover NO head/tail bands, NO ribbon, NO custom endpapers (Mixam yes; not in scope)
- KDP says cream NOT available for hardcover; lessons-learned uses cream (§4 C1); default to lessons-learned, validate at Previewer
- PIL `img.save("...", "PDF", ...)` produces imprecise MediaBox; use PyMuPDF `fitz` (G19)

---

## 2d. Paperback / softback, KDP perfect-bound (full spec)

### 2d.1 Interior file

| Spec | Value |
|---|---|
| **File format** | `.pdf` (preferred) or `.docx`. PDF for control. Generated via Word COM |
| **Trim / page size** | **6.00" × 9.00"** (8640 × 12960 DXA in docx; 432 × 648 pts in PDF) |
| **Top margin** | 0.5" (720 DXA) — exceeds KDP minimum of 0.25"; aesthetic choice |
| **Bottom margin** | 0.625" (900 DXA) |
| **Inside / gutter margin** | 0.625" (900 DXA). KDP minimums: 0.375" (≤150pp), 0.5" (151-300pp), 0.625" (301-500pp), 0.75" (501-700pp), 0.875" (701-828pp). At ~200pp, the 0.5" minimum applies; Bo uses 0.625" (exceeds for breathing room and to match hardcover) |
| **Outside margin** | 0.5" (720 DXA) — exceeds KDP minimum of 0.25" |
| **Header inset** | 0 |
| **Footer inset** | 360 DXA (~0.25") below the bottom margin |
| **Mirror margins** | **REQUIRED.** `mirror: true` on the page properties of the body section. THEN inject `<w:mirrorMargins/>` into `word/settings.xml` via JSZip post-process. (G16) |
| **Bleed (interior)** | 0.125" if any element bleeds; otherwise no bleed required |
| **Body font** | Georgia 11pt |
| **Body line spacing** | 320 DXA (~1.4×) |
| **First-line indent** | 360 DXA (~0.25") |
| **Body color** | `#1A1A1A` |
| **Justification** | Justified |
| **Running header** | same as hardcover (centered, 7.5pt, `#AAAAAA`, characterSpacing 30, book title all-caps) |
| **Footer** | mirror-aligned page numbers (RIGHT on recto, LEFT on verso); 9pt, `#888888` |
| **Page numbering** | front matter unnumbered; body restarts at 1; Arabic |
| **Section break style** | `· · ·` |
| **Chapter / Part heading** | same as hardcover (Heading 1, all-caps, `\u2726` ornament beneath, ODD_PAGE recto) |
| **Drop caps** | not used (consistent with hardcover; see OPEN-DECISION-5) |
| **ToC** | print ToC, manual page-number entries (not hyperlinked) |
| **Front matter (paperback, slimmer convention)** | Page i (recto) Half-title; Page ii (verso) Blank; Page iii (recto) Full title page; Page iv (verso) Copyright; Page 1 (recto) Body begins (page numbers restart at 1). Paperback CAN use the slimmer 4-page front matter or the full 8-page hardcover sequence; Bo's prior three books use the **fuller 8-page sequence** for parity with hardcover (single source markdown drives both) |
| **Back matter** | About the Author (Kindle-style), optional colophon |
| **Image specs** | 300 DPI; embedded; CMYK preferred (or no profile); flattened transparency |
| **Hyperlinks** | not clickable in print; URLs in body as plain text or footnoted |
| **Embedded fonts** | REQUIRED |
| **Transparency flattening** | REQUIRED |
| **PDF/X** | NOT required; flat PDF accepted |
| **Page count constraints** | **24 pages minimum, 828 pages maximum** for paperback. *The Long Watch* targeting ~200pp |
| **Page count multiple** | **2** (even) |
| **Page count parity check** | `check_part_pages.py` (Word COM) — same as hardcover |
| **Trailing blank gotcha** | same as hardcover (G17) |
| **docx → PDF route** | Word COM (`win32com.client`, `FileFormat=17`) — same as hardcover |
| **Paper option** | **CREAM** (Bo's literary default, the warmer aesthetic) **or WHITE.** Cream changes spine math (0.0025 per page vs 0.002252 for white) |

### 2d.2 Cover file (KDP paperback)

| Spec | Value |
|---|---|
| **Cover file format** | single-wrap PDF (back + spine + front, left-to-right) |
| **Color profile** | CMYK preferred; KDP recommends no embedded profile |
| **DPI** | 300 |
| **Bleed** | **0.125" on all four outer edges** |
| **Spine width** | `pages × 0.0025"` (cream) or `pages × 0.002252"` (white). NO additional board addition (paperback has no boards) |
| **Wrap width formula** | `WRAP_W_IN = 0.125 + 6.00 + spine_w + 6.00 + 0.125` |
| **Wrap height formula** | `WRAP_H_IN = 0.125 + 9.00 + 0.125 = 9.25"` |
| **Worked example, 100pp cream** | spine 0.250"; wrap 12.500" × 9.250" |
| **Worked example, 104pp cream** | spine 0.260"; wrap 12.510" × 9.250" (validated, *The City and the Girl*) |
| **Worked example, 186pp cream** | spine 0.465"; wrap 12.715" × 9.250" (validated, *The Night Was Young*) |
| **Worked example, 200pp cream** | spine 0.500"; wrap 12.750" × 9.250" |
| **PDF MediaBox precision** | exact via PyMuPDF (`page = pdf.new_page(width=WRAP_W_IN * 72, height=WRAP_H_IN * 72)`); PIL is imprecise (G19) |
| **Maximum file size** | 650 MB; recommended ≤ 40 MB |
| **Quiet zone (typography keep-out from outer edge)** | bleed + 0.25" = **0.375"** from each outer edge |
| **Spine-text safe zone** | 0.0625" margin on each side of spine. For very narrow spines (<0.5"), reduce ornament size and use weight-700 double-draw for visual bold (G5) |
| **Spine text minimum** | KDP requires **at least 79 pages** for spine text |
| **Front cover content** | same as hardcover (title, subtitle optional, author) |
| **Back cover content** | tagline, pull-quote, blurb body (150-200 words), closing byline |
| **Back cover image treatment** | darkened to ~75% black (alpha 184-210), same AI-art as front |
| **Spine content** | title + ornament + author, rotated -90°, cream-on-umber/navy |
| **ISBN placement** | back cover, bottom-right; KDP auto-generates EAN-13 barcode |
| **ISBN barcode keep-out** | **2.25" × 1.50"** at bottom-right of back cover panel |
| **Author bio / photo** | optional on back cover; *The Night Was Young* used a paragraph; *City* and *Second Notebook* did not. OPEN-DECISION-6 |
| **Imprint logo** | optional; not used on prior three Bo books |
| **Cover finish** | matte or glossy laminate. KDP defaults gloss; matte is selectable. **Matte recommended for literary fiction** (matches Bo's prior choice for Mixam hardcovers) |
| **Paper option for cover** | the cover is on standard cover stock; paper choice (cream/white) applies only to the INTERIOR |

### 2d.3 Metadata (Paperback)

Mostly mirrors Kindle/hardcover. Differences:

| Spec | Value |
|---|---|
| **ISBN** | REQUIRED. Separate from hardcover and Kindle. Free KDP or owned Bowker |
| **Imprint** | tied to ISBN |
| **Description** | shared on the bundled Amazon page with hardcover (single product listing carries both formats) |
| **Keywords** | shared (7 keywords) |
| **Categories** | shared (up to 3) |
| **Series info** | same |
| **Audience** | same (Adult) |
| **Pre-order** | NOT AVAILABLE for paperback. Only Kindle |
| **Publication date** | settable |

### 2d.4 Distribution (Paperback)

| Channel | Available? | Notes |
|---|---|---|
| **Amazon (global marketplaces)** | yes | default |
| **Expanded Distribution** | **YES (opt-in)** | reaches Ingram catalog → libraries, bookstores. Royalty drops to 40% (from 60%). $0/year setup (free; old setup fee waived). Returnable through some channels. **For Bo: NOT a fit** because of low margin and the Bowker ISBN dependency if Bo wants real Ingram presence (free KDP ISBN works via Expanded Distribution but with imprint = "Independently published") |
| **Library lending** | via Expanded Distribution only | |
| **Returnable** | YES (when Expanded Distribution enabled); otherwise N/A for Amazon-only |

### 2d.5 Pricing (Paperback)

| Tier | Value |
|---|---|
| **Royalty rate (Amazon channel)** | 60% of list minus printing cost |
| **Royalty rate (Expanded Distribution)** | 40% of list minus printing cost |
| **Print cost (US, B&W, 6×9)** | $0.85 fixed + $0.012 per page |
| **Print cost example (186pp B&W)** | $0.85 + (186 × $0.012) = $3.082 |
| **Print cost example (200pp B&W)** | $0.85 + (200 × $0.012) = $3.25 |
| **Min list price (US)** | calculated to give ≥ $0.01 royalty. For 200pp B&W on 60% channel: minimum ≈ $5.42. KDP shows the floor at submission |
| **Max list price (US)** | no posted ceiling; pragmatic ~$50 |
| **Royalty example (200pp, $14.99, Amazon channel)** | $14.99 × 0.6 − $3.25 = $8.99 − $3.25 = **$5.74 per sale** |
| **Royalty example (200pp, $14.99, Expanded Distribution)** | $14.99 × 0.4 − $3.25 = $6.00 − $3.25 = **$2.75 per sale** |
| **Print cost (premium color)** | $0.85 fixed + $0.07 per page (US). 200pp color: $14.85 print cost |

### 2d.6 Paperback-specific gotchas

- Free KDP ISBN cannot be used elsewhere (e.g., IngramSpark requires its own)
- Expanded Distribution drops royalty 60% → 40%
- Mirror margins silently dropped by `docx@9` — inject via JSZip (G16)
- Trailing EVEN_PAGE blank trips margin validator (G17)
- Narrow spine (<0.5") requires double-draw weight-700 text (G5)
- PIL imprecise MediaBox; use PyMuPDF (G19)
- Cover wrap math: never reuse covers across services (paperback vs Mixam vs KDP hardcover; spine widths differ) (G3)

---

## 3a. Interior file specs side-by-side

| Dimension | Kindle | Digital PDF | Hardcover | Paperback |
|---|---|---|---|---|
| **File format** | DOCX | PDF (PyMuPDF) | PDF (Word COM) | PDF (Word COM) |
| **Page size** | reflowable | 6.00" × 9.00" | 6.00" × 9.00" | 6.00" × 9.00" |
| **Top margin** | 1.0" suggestion | 0.5" inherited | 0.5" | 0.5" |
| **Bottom margin** | 1.0" suggestion | 0.625" inherited | 0.625" | 0.625" |
| **Inside/gutter** | 1.0" suggestion | 0.625" inherited | 0.625" | 0.625" |
| **Outside margin** | 1.0" suggestion | 0.5" inherited | 0.5" | 0.5" |
| **Mirror margins** | FORBIDDEN | inherited (cosmetic) | REQUIRED | REQUIRED |
| **Bleed** | N/A | 0 (cover crop) | 0.125" if needed | 0.125" if needed |
| **Body font** | Georgia 11pt (override-able) | Georgia 11pt (fixed) | Georgia 11pt | Georgia 11pt |
| **Line spacing** | 320 DXA | 320 DXA inherited | 320 DXA | 320 DXA |
| **First-line indent** | 360 DXA | 360 DXA inherited | 360 DXA | 360 DXA |
| **Body color** | `#1A1A1A` | `#1A1A1A` | `#1A1A1A` | `#1A1A1A` |
| **Justification** | Justified (reader override) | Justified | Justified | Justified |
| **Running header** | none | inherited | yes | yes |
| **Page numbers** | none | inherited | Arabic on body | Arabic on body |
| **Page-number font** | n/a | inherited | 9pt Georgia `#888888` | 9pt Georgia `#888888` |
| **Page-number alignment** | n/a | inherited | mirror (R on recto, L on verso) | mirror (R on recto, L on verso) |
| **Front matter sequence** | lean (title, copyright, dedication, epigraph, ToC) | print sequence minus stripped | full 8-page (half-title, blank, title, copyright, dedication, blank, epigraph, blank) | same as hardcover |
| **Front matter pages stripped** | n/a (it's the source) | strip p2, p3, p4 (blank verso, title page, copyright) | none | none |
| **Recto/verso enforcement** | none | inherited | each Part on recto (ODD_PAGE) | each Part on recto (ODD_PAGE) |
| **Section break ornament** | `· · ·` | `· · ·` (inherited) | `· · ·` | `· · ·` |
| **Part heading ornament** | `\u2726` ✦ | `\u2726` (inherited) | `\u2726` | `\u2726` |
| **ToC** | hyperlinked, auto-built from H1 | inherited (not hyperlinked) | manual, not hyperlinked | manual, not hyperlinked |
| **Image DPI** | 300 recommended | 300 inherited | 300 | 300 |
| **Image color profile** | sRGB | sRGB | CMYK / no profile | CMYK / no profile |
| **Hyperlinks** | LIVE | LIVE (PDF preserves) | dead | dead |
| **Embedded fonts** | n/a | yes | yes | yes |
| **Transparency** | n/a | flat | flat | flat |
| **PDF/X** | n/a | not required | not required | not required |
| **Spot colors** | n/a | n/a | not supported | not supported |
| **Page count constraint** | irrelevant | matches print PDF | 75-550, multiple of 2 | 24-828, multiple of 2 |
| **Reflowable vs fixed** | reflowable | fixed | fixed | fixed |
| **Math character font** | `Cambria Math` required | inherited | inherited | inherited |
| **Code span font** | `Consolas` | inherited | inherited | inherited |

---

## 3b. Cover file specs side-by-side

| Dimension | Kindle | Digital PDF | Hardcover (KDP) | Paperback (KDP) |
|---|---|---|---|---|
| **Cover format** | single JPEG/TIFF | 2 PDF pages | single-wrap PDF | single-wrap PDF |
| **Panels** | front only | front + back (separate pages) | back + spine + front (one wrap) | back + spine + front (one wrap) |
| **Cover dimensions (200pp cream example)** | 1600 × 2560 px | 6×9 + 6×9 | 14.264" × 10.417" | 12.75" × 9.25" |
| **Aspect ratio** | 1.6:1 | trim only | wrap | wrap |
| **Bleed/wrap** | none | 0 (cropped) | 0.708" wrap | 0.125" bleed |
| **Spine width formula** | n/a | n/a | `pages × 0.0025 + 0.348"` (cream) | `pages × 0.0025"` (cream) |
| **Spine boards addition** | n/a | n/a | **+0.348"** (current; was 0.302" old; Amazon docs say 0.06") | n/a |
| **Wrap height** | n/a | 9.00" | **10.417"** (KDP-rounded, not arithmetic 10.416) | 9.250" |
| **Color profile** | RGB / sRGB | sRGB | CMYK preferred, no profile recommended | same |
| **DPI** | 300 recommended | 300 | 300 | 300 |
| **JPEG quality** | ≥ 80 | 92 | 95 | 95 |
| **Max file size** | < 50 MB | (no constraint; aim < 5 MB) | 650 MB (≤40 MB recommended) | same |
| **Quiet zone** | n/a | n/a | bleed + 0.25" = 0.958" from outer edge | bleed + 0.25" = 0.375" from outer edge |
| **Spine-text safe zone** | n/a | n/a | 0.0625" each side of spine | 0.0625" each side of spine |
| **Spine text minimum page count** | n/a | n/a | 79pp | 79pp |
| **ISBN barcode keep-out** | n/a | n/a | 2.25" × 1.50" bottom-right of back | 2.25" × 1.50" bottom-right of back |
| **Front content** | title, author | title, author | title, author | title, author |
| **Back content** | n/a | tagline, blurb, byline (carries ISBN if not masked) | tagline, blurb, byline | tagline, blurb, byline |
| **Spine content** | n/a | n/a | title + ornament + author, rotated -90° | title + ornament + author, rotated -90° |
| **Dust jacket** | n/a | n/a | NO | n/a |
| **Endpapers** | n/a | n/a | white stock only | n/a |
| **Head/tail bands** | n/a | n/a | NO | n/a |
| **Bookmark ribbon** | n/a | n/a | NO | n/a |
| **Lamination** | n/a | n/a | matte or glossy (default) | matte or glossy (default) |
| **MediaBox precision tool** | n/a | PyMuPDF | PyMuPDF (PIL imprecise) | PyMuPDF (PIL imprecise) |
| **Cover source script** | front-only PIL or external | `build_digital_*.py` | `composite_cover_*_kdp_hardcover.py` | `composite_cover_*_kdp.py` |
| **Title font** | Cormorant Garamond Light, baked | inherited from print | Cormorant Garamond Light | Cormorant Garamond Light |
| **Title size** | varies by design | inherited | ~7.5% of wrap height | ~7.5% of wrap height |
| **Author size** | varies by design | inherited | ~3.5% of wrap height | ~3.5% of wrap height |
| **Cover palette (navy variant)** | navy `#0D1B2A`, cream `#F4EFE0`, gold `#C9A760` | inherited | same | same |

---

## 3c. Metadata specs side-by-side

| Dimension | Kindle | Digital PDF | Hardcover (KDP) | Paperback (KDP) |
|---|---|---|---|---|
| **Identifier** | ASIN (auto-assigned) | none | ISBN (free KDP or owned) | ISBN (free KDP or owned) |
| **ISBN required?** | NO | NO | YES | YES |
| **ISBN must differ per format?** | n/a | n/a | YES (separate from paperback) | YES (separate from hardcover) |
| **Title** | up to 200 char | optional PDF metadata | shared with Kindle (same product page) | shared |
| **Subtitle** | up to 200 char | optional | shared | shared |
| **Author** | full author name | optional | shared | shared |
| **Description** | up to 4000 char | n/a | shared with Kindle on bundled listing | shared |
| **Keywords** | 7 × 50 char | n/a | shared 7 | shared 7 |
| **Categories** | up to 3 | n/a | shared up to 3 | shared up to 3 |
| **BISAC** | derived from category | n/a | derived from category | derived from category |
| **Audience** | Adult | n/a | Adult | Adult |
| **Reading age** | optional | n/a | optional | optional |
| **Language** | EN | n/a | EN | EN |
| **DRM** | toggle (immutable after first publish) | n/a (no DRM) | n/a | n/a |
| **Pre-order** | yes, up to 1 year | n/a | NO | NO |
| **Imprint** | free KDP → "Independently published"; owned ISBN → custom | optional in PDF metadata | tied to ISBN | tied to ISBN |
| **Publication date** | settable | n/a | settable | settable |
| **Series info** | optional | n/a | optional, shared | optional, shared |
| **Adult-content flag** | toggle | n/a | toggle | toggle |
| **Updates push to existing buyers** | no, opt-in via "Manage Your Content" | n/a | n/a (physical) | n/a (physical) |

---

## 3d. Distribution / channel specs side-by-side

| Dimension | Kindle | Digital PDF | Hardcover (KDP) | Paperback (KDP) |
|---|---|---|---|---|
| **Amazon US** | yes | n/a (direct) | yes | yes |
| **Amazon International (UK, DE, FR, ES, IT, JP, BR, MX, AU, NL, CA, IN)** | yes | n/a | yes | yes |
| **Kindle Unlimited (KU)** | optional (requires KDP Select 90-day exclusivity) | n/a | n/a | n/a |
| **Expanded Distribution (Ingram, libraries, bookstores)** | n/a | n/a | **NO** | **YES (opt-in)** |
| **Pre-order** | yes | n/a | NO | NO |
| **Returnability** | n/a | n/a | yes (Amazon standard) | yes (if Expanded Distribution) |
| **Direct download (Bo's site)** | n/a | yes | n/a | n/a |
| **Hugging Face hosting** | n/a | yes (as bundle artifact) | n/a | n/a |
| **GitHub Releases hosting** | n/a | yes | n/a | n/a |
| **Library lending** | yes (Amazon library) | n/a | n/a (purchasable via Amazon Business) | yes (via Expanded Distribution) |

---

## 3e. Pricing / royalty specs side-by-side

| Dimension | Kindle | Digital PDF | Hardcover (KDP) | Paperback (KDP) |
|---|---|---|---|---|
| **Min list price (US)** | $0.99 | free | floor ≈ $13-15 (200pp B&W) | floor ≈ $5-6 (200pp B&W) |
| **Max list price (US)** | $200 | n/a | no posted ceiling | no posted ceiling |
| **Royalty rate (primary channel)** | 70% ($2.99-$9.99) or 35% (else) | n/a | 60% of list − print cost | 60% of list − print cost |
| **Royalty rate (Expanded Distribution)** | n/a | n/a | n/a | 40% of list − print cost |
| **Delivery fee** | $0.15 per MB (70% only) | n/a | n/a | n/a |
| **Print cost (200pp B&W example, US)** | n/a | n/a | $5.65 + 200 × $0.012 = $8.05 | $0.85 + 200 × $0.012 = $3.25 |
| **Print cost (200pp color premium, US)** | n/a | n/a | $5.65 + 200 × $0.065 = $18.65 | $0.85 + 200 × $0.07 = $14.85 |
| **Royalty example ($24.99 retail, 200pp, B&W, Amazon channel)** | (Kindle wouldn't be $24.99) | n/a | $24.99 × 0.6 − $8.05 = $6.94 | $24.99 × 0.6 − $3.25 = $11.74 |
| **Currency conversion** | auto per marketplace | n/a | auto per marketplace | auto per marketplace |
| **Free pricing** | only via KDP Select promo (5 days/90 days) | always free | n/a (physical) | n/a (physical) |

---

## 4. CONFLICT FLAGS

Each conflict lists both readings, recommended default (lessons-learned per Bo's instruction), and the open recalibration path.

### C1. Hardcover paper option: cream vs white

- **Lessons-learned (`book/production_lessons_learned.md` §6.1, §7.1, §19.3, plus prior scripts like `composite_cover_city_kdp_hardcover.py` line 32):** cream paper is used for hardcover; spine math = `pages × 0.0025` (cream) regardless of paperback/hardcover
- **Amazon docs (via kdpcoverlab.com extract):** "White paper only (no cream available for hardcover)"
- **kdpeasy.com confirmation:** "Cream paper is only available for paperback — hardcover (case laminate) uses white paper exclusively"
- **Default per Bo's instruction:** use cream. The prior three Bo books shipped cream-paper hardcovers through KDP successfully (the lessons-learned doc and `composite_cover_*_kdp_hardcover.py` scripts confirm). It's possible Amazon's docs and third-party calculators reflect a paperback-only paper-stock restriction or a marketing simplification, while the actual submission system accepts cream on hardcover. **Validate at KDP Print Previewer first.** If rejected, fall back to white (spine math becomes `pages × 0.002252`)

### C2. Hardcover wrap (turn-in) dimensions: 0.708" vs 0.625" vs 0.591" vs 0.394"

- **Lessons-learned §7.1, §19.2, and all `composite_cover_*_kdp_hardcover.py` scripts:** 0.708" on all four outer edges
- **kdpcoverlab.com:** 0.625" wrap + 0.375" hinge channels
- **kdpeasy / general:** width = 2 × trim + spine + 0.394 + 2 × 0.591 (i.e., wrap = 0.591"; gutter additions = 0.394")
- **kdp.amazon.com docs (where extractable):** "0.125" (3.2 mm)" bleed mentioned (this is paperback bleed, conflated)
- **Default per Bo's instruction:** **use 0.708"**. This value is empirically validated against KDP Print Previewer rejections on *The Autotelic Disposition* and *The Night Was Young* builds. The 0.625" vs 0.591" vs 0.394" divergences in third-party sources suggest Amazon's spec moved (or third parties are approximating). The empirical record (a real-world rejection-then-accept cycle) wins
- **Recalibration path:** if KDP Print Previewer rejects with a different expected wrap value, use the literal value from the error message

### C3. Hardcover spine board addition: +0.348" vs +0.302" vs +0.06"

- **Lessons-learned §8.2, §19.3, and current scripts (`composite_cover_city_kdp_hardcover.py` line 39, `composite_cover_second_notebook_kdp_hardcover.py` line 27):** +0.348" (current, post-April 2026 calibration)
- **Old `C:\Claude-Titanic\PRODUCTION_LESSONS_LEARNED.md` (April 20, 2026):** +0.302"
- **kdpcoverlab.com (Amazon-derived):** +0.06" (paperback-like; "spine = (200 × 0.002252) + 0.06 = 0.5104 inches")
- **Default per Bo's instruction:** **use 0.348"**. The Titanic-era 0.302" was superseded empirically. The 0.06" Amazon-docs value appears to be either a paperback-spine-with-cover-thickness number wrongly applied to hardcover, or an old hardcover spec that Amazon has not corrected
- **Recalibration path:** if KDP Print Previewer rejects, take the literal expected spine from the error and back-solve the board-add value

### C4. Hardcover wrap height: 10.416" vs 10.417"

- **Arithmetic:** 9.00 + 0.708 × 2 = 10.416"
- **KDP validator:** 10.417"
- **Lessons-learned and all scripts:** override to 10.417"
- **Default:** 10.417" (lessons-learned and KDP-empirical agree; arithmetic loses)

### C5. KDP Kindle cover aspect ratio: 1.6:1 vs other

- **Amazon docs:** ideal 2560 × 1600 px = 1.6:1 (height/width); minimum 1000 × 625
- **Lessons-learned §10:** says "1.6:1" — agrees
- **No conflict; included for completeness**

### C6. KDP paperback interior gutter at ~200pp: 0.625" (Bo) vs 0.5" (KDP minimum)

- **Lessons-learned §6.1:** 0.625" gutter (paperback, 12pt body)
- **Amazon docs:** minimum 0.5" for 151-300pp books
- **Resolution:** Bo's value EXCEEDS the minimum; not a conflict. 0.625" is for aesthetic breathing room. No action needed

### C7. Paper for paperback: cream (Bo) vs cream-or-white-by-publisher-choice (Amazon)

- **Lessons-learned:** cream is default for literary fiction (used in all three prior Bo books)
- **Amazon:** both available; publisher choice
- **No conflict; Bo's choice stands**

### C8. Font size: 11pt vs 12pt body

- **Lessons-learned §17 C4:** *The Night Was Young* used 12pt with 340 DXA line spacing; *City* and *Second Notebook* used 11pt with 320 DXA
- **Resolution per lessons-learned:** per-book aesthetic call. Both pass KDP. For *The Long Watch*: OPEN-DECISION-1
- **No conflict; stylistic choice**

### C9. Front matter sequence: 4-page vs 8-page

- **Hardcover convention:** 8-page (half-title, blank, title, copyright, dedication, blank, epigraph, blank)
- **Paperback slimmer convention:** 4-page (half-title, blank, title, copyright)
- **Bo's prior practice:** uses the fuller 8-page sequence for both paperback and hardcover (single source markdown drives both)
- **No conflict; consistency choice — recommend continuing 8-page for *The Long Watch***

### C10. ISBN ownership: free KDP vs Bowker

- **Free KDP ISBN:** belongs to Amazon (technically); forces "Independently published" imprint; cannot be used elsewhere (Ingram/Bowker reject)
- **Bowker ISBN:** $125-295 each (10-pack cheaper per unit); fully Bo-owned; allows custom imprint and IngramSpark cross-listing
- **Lessons-learned §13.7:** notes the trade-off; doesn't resolve. Prior three Bo books used free KDP ISBNs
- **No conflict; explicit OPEN-DECISION-2**

### C11. Mixam relevance for *The Long Watch*

- **Lessons-learned §9 covers Mixam extensively** as a premium hardcover route
- **Task scope:** four versions = Kindle, Digital PDF, KDP hardcover, KDP paperback. **Mixam is NOT one of the four.**
- **Resolution:** Mixam is out of scope for this listing. Mixam-specific 0.80" cover bleed, 3-panel separated PDFs, 0.875" gutter, etc. are documented in lessons-learned but not reproduced here. If Bo later wants a Mixam edition (personal/gift/archival), see lessons-learned §6.2, §7.2, §9

### C12. Kindle DRM default

- **Amazon:** DRM is optional on first publish; once set, cannot be changed
- **Bo's open-source ethos:** suggests DRM-free
- **Resolution:** OPEN-DECISION-7

---

## 5. OPEN DECISIONS (Bo needs to call)

### OPEN-DECISION-1: Body font size — 11pt or 12pt?

| Option | Implication |
|---|---|
| **11pt, 320 DXA leading** | Tighter pages, fewer pages, ~$0.024 less print cost per copy at 200pp paperback. *City* and *Second Notebook* pattern |
| **12pt, 340 DXA leading** | More breathing room, more pages, ~$0.024 more print cost per copy. *The Night Was Young* pattern |

For literary fiction at 50K-60K words, **11pt is the more common modern indie choice**; 12pt reads as more deliberate / archival. Bo's call.

### OPEN-DECISION-2: ISBN strategy — free KDP or owned Bowker?

| Option | Implication |
|---|---|
| **Free KDP ISBN per format** | Free. Imprint forced to "Independently published". Cannot cross-list to IngramSpark with same ISBN. Acceptable for ASTRA-7 open-source ethos. Prior three Bo books did this |
| **Owned Bowker ISBNs (10-pack)** | ~$295 for 10 = $29.50 per ISBN. Custom imprint allowed. Cross-listable. More professional appearance. *The Long Watch* uses 3 ISBNs (paperback, hardcover, Kindle); the 10-pack supports up to 10 future Bo books |

ASTRA-7 ethos doesn't preclude owned ISBNs; the free KDP route is fine. **Default recommendation:** free KDP ISBNs for Phase 1; revisit if IngramSpark/library distribution becomes a goal.

### OPEN-DECISION-3: Digital PDF back cover — keep or mask ISBN barcode?

| Option | Implication |
|---|---|
| **Keep barcode visible** | The back cover panel is a faithful photo of the printed book. Maintains "this is the real book" authenticity. Tells reader where to buy if they want the physical. Prior Bo digital PDFs did this |
| **Mask barcode** | Cleaner aesthetic; barcode area becomes empty cream or absorbs into the darkened back image. Implementation: edit the back-panel JPG in PIL after `extract_back_cover_trim()` and before saving |

**Default recommendation:** keep barcode (matches prior books, maintains the authenticity register).

### OPEN-DECISION-4: Digital PDF metadata — set or leave blank?

PyMuPDF supports `pdf.set_metadata({"title": "...", "author": "Bo Chen", "subject": "...", "keywords": "..."})` before `pdf.save()`. The current `build_digital_*.py` scripts do NOT set this. **Recommendation:** set Title, Author, Subject (one-line synopsis), Keywords. This lets PDF readers and Google Drive index correctly.

### OPEN-DECISION-5: Drop caps on chapter / Part openings?

Prior three Bo books: NO drop caps. **Recommendation:** keep no-drop-caps for stylistic consistency. *The Long Watch* register is the same family.

### OPEN-DECISION-6: Author photo on back cover or in author bio?

- **Lessons-learned §13.4:** "Don't include an author photo if the author is camera-shy — Bo's bio has no photo"
- **Recommendation:** no photo, prior practice carries.

### OPEN-DECISION-7: Kindle DRM toggle

- **Recommendation:** DRM-free for ASTRA-7 open-source ethos consistency.

### OPEN-DECISION-8: Paperback Expanded Distribution opt-in?

- **Royalty:** drops 60% → 40%. Print cost unchanged.
- **Reach:** Ingram catalog (libraries, bookstores).
- **Lessons-learned:** prior Bo books not enabled (no notes on opt-in path).
- **Recommendation:** **disable**. The 40% royalty bites hard for a 200pp book ($5.74 → $2.75 per sale at $14.99). Library reach via Ingram is more valuable when there's also IngramSpark setup; with KDP-only Expanded Distribution and a "Independently published" imprint, library purchasers can find the book on Amazon anyway. Enable later if library marketing pushes for it.

### OPEN-DECISION-9: Kindle Select / Kindle Unlimited enrollment

- **KDP Select:** 90-day Amazon Kindle exclusivity. Enables KU lending (royalty per page read) and 5 free promo days per 90-day cycle.
- **ASTRA-7 ethos:** open distribution; **NOT exclusive**.
- **Recommendation:** **decline KDP Select**. Distribute Kindle via Amazon AND keep digital PDF available elsewhere.

### OPEN-DECISION-10: Cover finish (matte vs glossy laminate)

- **Both paperback and hardcover:** matte is selectable.
- **Lessons-learned §9.7:** "For literary fiction, matte is the default. Glossy reads as airport-thriller."
- **Recommendation:** **matte** for both KDP paperback and KDP hardcover.

### OPEN-DECISION-11: Page count target

- **Soft targets:** paperback at 11pt typically converges around 200pp for a 50-55K word novel. Hardcover same.
- **No hard call needed**; the page count emerges from the manuscript + font choice (OPEN-DECISION-1). Verify via `check_part_pages.py` (Word COM) once draft 1 is locked.

### OPEN-DECISION-12: Half-title text format

- **Convention:** book title only, all-caps, centered, smaller than full title page (22pt half-points = 11pt vs 36pt at full title).
- **Prior books:** consistent with this. **Recommendation:** continue.

### OPEN-DECISION-13: Color palette for *The Long Watch*

- **Prior palettes:** navy (`#0D1B2A`) for *The Night Was Young*; umber (`#120E16`) for *City* and *Second Notebook*.
- **For *The Long Watch* / ASTRA-7:** the hull aesthetic at `memory/hull_design_v0.md` is "faceted dark composite" — fits navy or near-black umber.
- **Recommendation:** establish the palette as part of cover design; not yet locked. Cover will likely use a navy-leaning dark with cream and gold accents, consistent with the space/starship register.

---

## 6. Sources cited

### 6.1 File paths (local)

- `C:\ASTRA-7\book\production_lessons_learned.md` — canonical lessons-learned (Bo's authority)
- `C:\ASTRA-7\book\CANON.md`, `book/negative_space.md`, `book/manuscript/` — *The Long Watch* primary documents (background)
- `C:\Claude-Titanic\PRODUCTION_LESSONS_LEARNED.md` — older lessons-learned (April 20, 2026); superseded
- `C:\Claude-Titanic\generate_book_kdp.js` — *The Night Was Young* KDP paperback generator
- `C:\Claude-Titanic\generate_kindle.js` — *The Night Was Young* Kindle generator
- `C:\Claude-Titanic\generate_book_v12.js` — *The Night Was Young* Mixam variant
- `C:\Claude-Titanic\generate_city_kdp.js` — *City* KDP paperback
- `C:\Claude-Titanic\generate_city_kindle.js` — *City* Kindle
- `C:\Claude-Titanic\generate_second_notebook_kdp.js` — *Second Notebook* KDP paperback (canonical for paperback specs, font/margins/section structure)
- `C:\Claude-Titanic\generate_second_notebook_kindle.js` — *Second Notebook* Kindle (canonical for Kindle specs)
- `C:\Claude-Titanic\composite_cover_kdp.py` — *The Night Was Young* KDP paperback cover
- `C:\Claude-Titanic\composite_cover_kdp_hardcover.py` — *The Night Was Young* KDP hardcover (old +0.302" calibration)
- `C:\Claude-Titanic\composite_cover_city_kdp.py` — *City* paperback (current paperback cover canon)
- `C:\Claude-Titanic\composite_cover_city_kdp_hardcover.py` — *City* hardcover (current +0.348" hardcover board calibration)
- `C:\Claude-Titanic\composite_cover_second_notebook_kdp.py` — *Second Notebook* paperback cover
- `C:\Claude-Titanic\composite_cover_second_notebook_kdp_hardcover.py` — *Second Notebook* hardcover
- `C:\Claude-Titanic\build_digital_pdf.py` — *Night Was Young* digital PDF assembler
- `C:\Claude-Titanic\build_digital_city.py` — *City* digital PDF (canonical pattern: strip {2,3,4} front-matter pages)
- `C:\Claude-Titanic\build_digital_second_notebook.py` — *Second Notebook* digital PDF
- `C:\Claude-Titanic\check_part_pages.py` — Word COM pagination verifier
- `C:\Claude-Titanic\lint_manuscript.py` — markdown corruption-signature linter
- `C:\Claude-Titanic\fonts\CormorantGaramond-Light.ttf` — cover font (variable axis)
- `C:\Claude-Titanic\fonts\CormorantGaramond-Bold.ttf` — cover font bold variant
- `C:\Claude-Titanic\the_city_and_the_girl\` — *City* book project
- `C:\Claude-Titanic\the_night_was_young_cover_kdp_hardcover\cover_wrap_hardcover.pdf` — actual shipped hardcover wrap (validator-confirmed)
- `C:\Claude-Titanic\the_second_notebook\` — *Second Notebook* project

### 6.2 URLs (current Amazon KDP, accessed May 2026)

- `https://kdp.amazon.com/en_US/help/topic/G201953020` — KDP paperback cover specifications (bleed, spine formulas, file format, color profile, DPI)
- `https://kdp.amazon.com/en_US/help/topic/G200645690` — KDP eBook cover image specifications (dimensions, aspect ratio, file format, color profile, DPI, max file size)
- `https://kdp.amazon.com/en_US/help/topic/G202145400` — KDP eBook manuscript formatting (partial coverage)
- `https://kdp.amazon.com/en_US/help/topic/GHT976ZKSKUXBB6H` — KDP hardcover printing cost formula
- `https://kdp.amazon.com/en_US/help/topic/G201834330` — KDP paperback royalty
- `https://kdp.amazon.com/en_US/help/topic/G201834280` — KDP paperback and hardcover distribution rights
- `https://kdp.amazon.com/en_US/help/topic/GQTT4W3T5AYK7L45` — KDP Expanded Distribution
- `https://kdp.amazon.com/en_US/help/topic/G200644210` — KDP eBook royalties (35% / 70%)
- `https://kdp.amazon.com/en_US/help/topic/G200634500` — KDP digital book pricing
- `https://kdp.amazon.com/en_US/help/topic/G200634560` — KDP eBook list price requirements
- `https://kdp.amazon.com/en_US/help/topic/G201189630` — KDP write a book description
- `https://kdp.amazon.com/en_US/help/topic/G201834170` — KDP ISBN and imprint
- `https://kdp.amazon.com/en_US/help/topic/G201834260` — KDP fix paperback and hardcover formatting issues
- `https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6` — KDP set trim size, bleed, and margins
- `https://kdp.amazon.com/en_US/help/topic/G201953400` — KDP hardcover cover specifications (URL returns 404 as of May 2026; data inferred from other sources)
- `https://kdp.amazon.com/cover-calculator` — KDP cover calculator (official tool; recommended as the final-authority dimension validator)

### 6.3 Third-party sources

- `https://www.kdpcoverlab.com/kdp-cover-size-guide.html` — 2026 KDP cover size guide (paperback + hardcover)
- `https://www.kdpeasy.com/blog/spine-width-calculator-guide` — spine width formula reference
- `https://www.kdpeasy.com/guides/2026-kdp-royalty-rates` — 2026 royalty rates summary
- `https://www.kdpeasy.com/tools/kdp-cover-size-calculator` — third-party cover calculator
- `https://bookcoverslab.com/kdp-cover-size-calculator` — third-party cover calculator
- `https://bookcoverslab.com/kdp-cover-templates/6x9-paperback` — 6×9 paperback template guide
- `https://kdpformatters.com/kdp-gutter-calculator/` — gutter margin requirements by page count
- `https://kdpformatters.com/kdp-paperback-margins/` — paperback margin guide
- `https://kindlepreneur.com/book-gutter/` — book gutter formatting
- `https://www.automateed.com/kdp-cover-dimensions` — third-party cover dimension calculator
- `https://www.automateed.com/kdp-printing-cost-calculator` — 2026 printing cost calculator
- `https://www.kdpcoverlab.com/kdp-spine-calculator.html` — 2026 spine calculator
- `https://www.creatorformat.com/blog/kdp-cover-dimensions-spine-width-calculator-guide` — 2025/2026 cover dimensions guide
- `https://www.inkfluenceai.com/learn/paperback-publishing-kdp-print` — 2026 paperback publishing guide

---

## End of document

**Length target:** ~10K words. Actual: ~9,500 words.

**Status:** complete; conflict-flagged where empirical (Bo's three-book corpus) and Amazon docs disagree. Lessons-learned wins per Bo's instruction in all conflicts.

**Next action:** when *The Long Watch* enters production, use this document as the per-version spec sheet. Validate against KDP Print Previewer for the hardcover wrap (C2) and the cream-paper option (C1). Update §4 in place if Previewer rejects with a different expected dimension.
