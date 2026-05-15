# Cover Art Specifications

*Authoritative cover specs for The Long Watch across all four publication formats. All formats use 6" × 9" trim size.*

*Empirical numbers derived from the Inside_The_Region production cycle (May 2026), validated against KDP Print Previewer acceptance after multiple rejection iterations.*

---

## Cover Files Required

| File | Format | Purpose |
|------|--------|---------|
| `cover_source.png` | Source artwork (4000+ × 6000+ px recommended) | Front cover artwork at high resolution; used by composite scripts |
| `cover_kindle.jpg` | JPEG, sRGB, 1600 × 2560 px | Kindle ebook cover (front only) |
| `cover_kdp_paperback.pdf` | PDF, CMYK, 300 DPI | KDP paperback wrap (front + spine + back, with bleed) |
| `cover_kdp_hardcover.pdf` | PDF, CMYK, 300 DPI | KDP hardcover wrap (front + spine + back, with turn-in) |
| `cover_placeholder.png` | PNG, any size | Placeholder used during script development before final art exists |

---

## Per-Format Dimensions

### Kindle ebook cover (front-only)

| Spec | Value |
|------|-------|
| Pixel dimensions | 1600 × 2560 px |
| Aspect ratio | 1.6:1 |
| Color profile | sRGB |
| Format | JPEG (preferred) or TIFF |
| Quality | JPEG quality ≥ 80 |
| Max file size | 50 MB |
| Spine / back | None (front cover only) |

### KDP paperback wrap (page-count dependent)

| Spec | Value |
|------|-------|
| Bleed | 0.125" on all four sides |
| Spine width formula | `pages × 0.002252` inches (no board addition) |
| Wrap width | `12 + spine + 0.25` inches |
| Wrap height | `9 + 0.25` = 9.25" |
| Color profile | CMYK |
| Resolution | 300 DPI |
| Format | PDF |
| Paper options | White or cream (your call — cream is warmer for literary fiction) |

**Example for 200 pages:**
- Spine = 200 × 0.002252 = 0.4504"
- Wrap = 12.4504 + 0.25 = 12.7004" × 9.25"

### KDP hardcover wrap (page-count dependent)

| Spec | Value |
|------|-------|
| Turn-in | 0.708" on all four sides |
| Spine width formula | `pages × 0.0025 + 0.241` inches (empirical from Inside_The_Region v3 acceptance) |
| Wrap width | `12 + spine + 1.416` inches |
| Wrap height | 10.417" (KDP validator-rounded from arithmetic 10.416) |
| Paper | **WHITE ONLY** (cream not available for KDP hardcover; confirmed in production) |
| Color profile | CMYK |
| Resolution | 300 DPI |
| Format | PDF |
| Spine hinge safe area | 0.4" from spine boundary (content within may clip) |
| Text/image safe margin | 0.635" from any edge |
| ISBN barcode | **KDP auto-overlays** in 2"×1.2" zone, bottom-right of back panel. **DO NOT draw a placeholder.** |

**Example for 200 pages:**
- Spine = 200 × 0.0025 + 0.241 = 0.741"
- Wrap = 12 + 0.741 + 1.416 = 14.157" × 10.417"

---

## Critical lessons (from Inside_The_Region production)

1. **`scale_to_fit` not `scale_to_cover` for back artwork with edge content.** If the back cover has chat screenshots, framed text, or content near edges, scale-to-cover will clip it. Use scale-to-fit with letterbox.

2. **Hardcover spine math iterates.** Expect KDP Print Previewer to reject the first hardcover submission. Use KDP's stated expected dimension from the rejection error to refine the spine constant; the `+0.241` value here is empirical after three rejection cycles on Inside_The_Region.

3. **Title hinge clearance.** Hardcover spine hinge consumes ~0.4" of front-panel left edge. Title must shift right beyond pure-center, or be sized smaller with wider quiet zone. Inside_The_Region settled on `x_shift = 40 px` and title at `0.052 × TRIM_H_PX` with 0.6" quiet zone.

4. **No ISBN placeholder on hardcover back.** KDP automatically overlays the ISBN barcode regardless of cover art content. Reserving a cream rectangle leaves a visible empty box on the printed cover.

5. **Spine has no author byline (per prior books' aesthetic).** Spine title only. Vertical orientation. Cormorant Garamond Bold.

---

## Source Aesthetic

Per project canon at `memory/hull_design_v0.md`: the ASTRA-7 hull is a 280m × 78m × 22m blended-wing-body, integrated warp, deployable thermal radiator wings, internal centrifuge habitat, faceted dark composite.

**The hull is the intended front-cover image.** Source aesthetic at:
- `memory/hull_design_v0.md` (AutoCAD spec + AI-image prompt forms)

Alternative aesthetics (lower priority):
- Astronomical: dwarf at 47°, Vela-field, Cepheid, deep space minimalism
- Bridge interior: viewport, command chair, the cup at the position
- The greenhouse: row three, deck plate, ambient grow lights

The hull-on-cover ties book identity to project identity. Strongly recommended.

---

## Composition Notes

| Element | Treatment |
|---------|-----------|
| **Title** | "The Long Watch" — Cormorant Garamond Bold, ~110-130px on hardcover, auto-fit with quiet zone |
| **Subtitle** | None (the book has no subtitle) |
| **Author** | "Bo Chen" — Cormorant Garamond Bold, ~70-80px, bottom of front cover |
| **Spine title** | "THE LONG WATCH" — vertical, Cormorant Garamond Bold, centered, double-drawn for thickness |
| **Spine author** | None per project convention |
| **Spine ornaments** | ✦ (four-pointed star) near top and bottom ends |
| **Back cover** | Per `book/back_cover.md` content; design TBD |

---

## File Paths

- `book/cover_art/SPECS.md` — this file
- `book/cover_art/cover_source.png` — source artwork (high-res, TBD)
- `book/cover_art/cover_placeholder.png` — placeholder for script development
- `book/cover_art/cover_kindle.jpg` — final Kindle cover (generated by composite_cover_kindle.py)
- `book/cover_art/cover_kdp_paperback.pdf` — final paperback wrap (generated by composite_cover_kdp_paperback.py)
- `book/cover_art/cover_kdp_hardcover.pdf` — final hardcover wrap (generated by composite_cover_kdp_hardcover.py)
