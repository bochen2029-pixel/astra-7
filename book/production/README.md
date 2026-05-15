# Production scripts — The Long Watch

*Simplified from Inside_The_Region's May 2026 production toolchain. Reference backup of the full Inside_The_Region scripts is in `_reference_inside_the_region/`.*

## Build sequence

All commands run from this directory (`C:\ASTRA-7\book\production`).

### 0. One-time setup

```
npm install     # installs docx@9.6.1 + jszip@3.10.1
```

Requires Windows + Microsoft Word + `pywin32` for Word COM. Requires Python with `python-docx`, `Pillow`, `PyMuPDF` (`fitz`).

### 1. Print interior (paperback + hardcover share this)

```
node generate_book_kdp_hardcover.js    # produces DOCX with TOC placeholder
python update_hardcover_and_count.py   # populates TOC, saves DOCX + PDF, reports page count
```

Output: `outputs/kdp_print/The_Long_Watch_PRINT_INTERIOR.docx` + `.pdf`

Note the printed page count from step 1 — it drives the cover spine math in step 3.

### 2. Kindle interior

```
node generate_kindle.js                # produces Kindle DOCX with TOC placeholder
python update_kindle_toc.py             # populates TOC field
```

Output: `outputs/kindle/The_Long_Watch_KINDLE.docx`

### 3. Covers

Before running, update `PAGES = N` in both `composite_cover_kdp_paperback.py` and `composite_cover_kdp_hardcover.py` with the count from step 1.

```
python composite_cover_kindle.py        # Kindle front cover (1600x2560 JPG)
python composite_cover_kdp_paperback.py # Paperback wrap PDF
python composite_cover_kdp_hardcover.py # Hardcover wrap PDF
```

Outputs in `outputs/kindle/` and `outputs/kdp_print/`.

### 4. Digital PDF

```
python build_digital_with_covers.py    # prepends covers to print interior PDF
```

Output: `outputs/digital/The_Long_Watch_DIGITAL.pdf`

## Source files

Read from `C:\ASTRA-7\book\manuscript\`:

- `front_NN_*.md` (front matter stubs — see those files for content state)
- `cycle_NN_*.md` (14 cycle files, existing)
- `back_NN_*.md` (back matter stubs)

The generators emit H1 chapter titles ("Cycle One" through "Cycle Fourteen") from the cycle number. Cycle files themselves start directly with prose (no H1 in source).

## Cover art

In `C:\ASTRA-7\book\cover_art\`:

- `SPECS.md` — authoritative cover dimensions per format
- `cover_placeholder.png` — navy 1600×2560 PNG used until real art exists
- `cover_source.png` — front cover artwork (when ready; replaces placeholder)
- `back_cover.png` — back cover artwork (optional; if absent, scripts use placeholder)

Composite scripts fall back to `cover_placeholder.png` if `cover_source.png` isn't present, so the pipeline is runnable end-to-end before real art exists.

## What was simplified out

Inside_The_Region's generators handled math, code blocks, pipe tables, bullet/numbered lists, blockquotes, and complex appendix structures. The Long Watch uses none of these — only prose paragraphs, italic/bold inline, H1 chapter titles, and section breaks (· · ·). The simplified generators are accordingly narrower.

If The Long Watch ever needs the dropped capabilities, restore from `_reference_inside_the_region/`.

## Canonical specs preserved from Inside_The_Region

Validated against KDP Print Previewer acceptance:

- **Hardcover spine:** `pages × 0.0025 + 0.241` (white paper, with boards)
- **Paperback spine:** `pages × 0.002252` (white paper, no boards)
- **Hardcover wrap height:** 10.417" (KDP validator-rounded from 10.416)
- **Hardcover turn-in:** 0.708" all sides
- **Paperback bleed:** 0.125" all sides
- **Print interior margins:** top 0.5" / bottom 0.625" / gutter 0.875" / outside 0.5"
- **Mirror margins:** explicit JSZip injection of `<w:mirrorMargins/>` into `word/settings.xml` (docx@9 drops the per-section flag)
- **Empty headers/footers:** explicitly required on every blank section to prevent "text outside margins" rejection (KDP detects inherited running header on trailing blank pages)
- **Spine hinge safe area:** 0.4" from spine (hardcover)
- **No ISBN barcode placeholder:** KDP auto-overlays bottom-right of back panel
- **Back cover scaling:** `scale_to_fit` (not `scale_to_cover`) when back artwork has content at edges

## Expect KDP rejection-driven iteration

Inside_The_Region went through v1 → v2 → v3 → v4 before KDP accepted the hardcover. Expect 2-4 Print Previewer iterations on the first build. When KDP rejects, it states expected dimensions in the error; use those to refine the spine math.
