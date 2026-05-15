"""
Composite the SINGLE-WRAP cover for Amazon KDP CASE LAMINATE HARDCOVER.

The Long Watch — 6x9 hardcover, white paper, ASTRA-7 minimal design.

DESIGN:
  - Entire wrap is dark navy (#0D1B2A), matching the Kindle cover.
  - Front panel: hex logo + "ASTRA-7" wordmark, centered, white.
    Same wordmark as the Kindle cover (Inter SemiBold).
    NOTHING ELSE — no book title, no author, no other images.
  - Spine: "THE LONG WATCH" vertical title, white. No author.
  - Back panel: description text from book/back_cover.md, rendered as
    clean typography in white/light-cream on the navy background.

Spine formula (empirical, post Inside_The_Region v3 KDP acceptance):
  Spine = pages * 0.0025 + 0.241

KDP disciplines preserved:
  - scale_to_fit (not scale_to_cover) for any image content
  - NO ISBN barcode placeholder (KDP auto-overlays bottom-right of back)
  - Spine hinge safe area: 0.4" from spine on each side of front/back
  - Text/image safe margin: 0.635" from any visible-trim edge

Output:
  C:\\ASTRA-7\\book\\production\\outputs\\kdp_print\\cover_wrap_hardcover.pdf
  C:\\ASTRA-7\\book\\production\\outputs\\kdp_print\\cover_wrap_hardcover.jpg (preview)
"""

import math
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# CONFIG
# ============================================================
DPI = 300
TRIM_W_IN = 6.00
TRIM_H_IN = 9.00

# Page count drives spine — update from update_hardcover_and_count.py output
PAGES = 186

# Spine math (empirical, validated against Inside_The_Region v3 KDP acceptance)
SPINE_PER_PAGE_HARDCOVER = 0.0025
SPINE_BOARDS_HARDCOVER = 0.241
SPINE_IN = round(PAGES * SPINE_PER_PAGE_HARDCOVER + SPINE_BOARDS_HARDCOVER, 4)

# Turn-in (KDP hardcover wrap)
WRAP_SIDE_IN = 0.708

# Total wrap dimensions
WRAP_W_IN = round(TRIM_W_IN * 2 + SPINE_IN + WRAP_SIDE_IN * 2, 4)
WRAP_H_IN = 10.417  # KDP validator-rounded

# Pixel canvas
WRAP_W = round(WRAP_W_IN * DPI)
WRAP_H = round(WRAP_H_IN * DPI)

# Panel pixel widths
WRAP_PX = round(WRAP_SIDE_IN * DPI)
TRIM_W_PX = round(TRIM_W_IN * DPI)
TRIM_H_PX = round(TRIM_H_IN * DPI)
SPINE_W_PX = WRAP_W - 2 * WRAP_PX - 2 * TRIM_W_PX

# Panel x-coordinates
BACK_X0 = WRAP_PX
BACK_X1 = BACK_X0 + TRIM_W_PX
SPINE_X0 = BACK_X1
SPINE_X1 = SPINE_X0 + SPINE_W_PX
FRONT_X0 = SPINE_X1
FRONT_X1 = FRONT_X0 + TRIM_W_PX

# Trim y-coordinates
TRIM_TOP = WRAP_PX
TRIM_BOTTOM = WRAP_H - WRAP_PX

# Safe margins (KDP hardcover)
SAFE_MARGIN_IN = 0.635
SAFE_MARGIN_PX = round(SAFE_MARGIN_IN * DPI)
SPINE_HINGE_IN = 0.4  # extra clearance from spine on front/back panels
SPINE_HINGE_PX = round(SPINE_HINGE_IN * DPI)

# Colors (ASTRA-7 brand)
NAVY = (13, 27, 42)        # #0D1B2A — background everywhere
WHITE = (255, 255, 255)
OFF_WHITE = (240, 240, 245)
SOFT_WHITE = (230, 230, 235)
DIM_WHITE = (200, 200, 210)

# Paths
ROOT = Path(r"C:\ASTRA-7")
BACK_COVER_MD = ROOT / "book" / "back_cover.md"

WIN_FONTS = Path(r"C:\Windows\Fonts")
FONT_SEMIBOLD = WIN_FONTS / "Inter-SemiBold.ttf"
FONT_MEDIUM = WIN_FONTS / "Inter-Medium.ttf"
FONT_REGULAR = WIN_FONTS / "Inter-Regular.ttf"
FONT_FALLBACK_BOLD = WIN_FONTS / "arialbd.ttf"
FONT_FALLBACK_REG = WIN_FONTS / "arial.ttf"

OUT_DIR = ROOT / "book" / "production" / "outputs" / "kdp_print"
OUT_DIR.mkdir(exist_ok=True, parents=True)
OUT_PDF = OUT_DIR / "cover_wrap_hardcover.pdf"
OUT_JPG = OUT_DIR / "cover_wrap_hardcover.jpg"

# Book metadata
WORDMARK = "ASTRA-7"
TITLE = "ASTRA-7: THE LONG WATCH"  # Full title (used on spine)
SPINE_TITLE = "ASTRA-7: THE LONG WATCH"  # Spine reads this top-to-bottom


# ============================================================
# Font helpers
# ============================================================
def font_semibold(size):
    return ImageFont.truetype(str(FONT_SEMIBOLD if FONT_SEMIBOLD.exists() else FONT_FALLBACK_BOLD), size=size)


def font_medium(size):
    return ImageFont.truetype(str(FONT_MEDIUM if FONT_MEDIUM.exists() else FONT_FALLBACK_REG), size=size)


def font_regular(size):
    return ImageFont.truetype(str(FONT_REGULAR if FONT_REGULAR.exists() else FONT_FALLBACK_REG), size=size)


# ============================================================
# Drawing helpers
# ============================================================
def measure_tracked(text, font, tracking_em):
    em = font.size
    widths = []
    for ch in text:
        bbox = font.getbbox(ch)
        w = bbox[2] - bbox[0] if bbox[2] > bbox[0] else em * 0.3
        widths.append(w)
    total = sum(widths) + (len(text) - 1) * em * tracking_em
    asc, desc = font.getmetrics()
    return int(total), int(asc + desc)


def draw_tracked(draw, xy, text, font, tracking_em, color):
    x, y = xy
    em = font.size
    cx = x
    for ch in text:
        draw.text((cx, y), ch, font=font, fill=color)
        bbox = font.getbbox(ch)
        w = bbox[2] - bbox[0] if bbox[2] > bbox[0] else em * 0.3
        cx += w + em * tracking_em


def draw_hexagon(draw, cx, cy, radius, color, stroke=6):
    """Regular hexagon outline centered at (cx, cy)."""
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 90)  # top vertex first
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        pts.append((x, y))
    pts.append(pts[0])
    draw.line(pts, fill=color, width=stroke, joint="curve")


def wrap_text(text, font, max_width):
    """Break text into lines fitting within max_width."""
    words = text.split()
    lines = []
    current = []
    current_w = 0
    space_bbox = font.getbbox(" ")
    space_w = space_bbox[2] - space_bbox[0]

    for word in words:
        word_bbox = font.getbbox(word)
        word_w = word_bbox[2] - word_bbox[0]

        if current and current_w + space_w + word_w > max_width:
            lines.append(" ".join(current))
            current = [word]
            current_w = word_w
        else:
            if current:
                current_w += space_w
            current.append(word)
            current_w += word_w

    if current:
        lines.append(" ".join(current))
    return lines


# ============================================================
# Parse back_cover.md into renderable paragraphs
# ============================================================
def parse_back_cover():
    """Read back_cover.md, return list of (text, style) tuples.
    Styles: 'pull_quote' | 'body' | 'tagline' | 'meta' | 'byline'."""
    md = BACK_COVER_MD.read_text(encoding="utf-8")
    # Skip everything before the first '---' separator
    parts = md.split("---", 1)
    body = parts[1] if len(parts) > 1 else parts[0]

    # Split into paragraphs by blank lines
    raw_paragraphs = re.split(r"\n\s*\n", body.strip())
    paragraphs = []
    for raw in raw_paragraphs:
        p = raw.strip()
        if not p:
            continue
        # Strip leading/trailing whitespace within
        p = p.replace("\n", " ").strip()

        # Detect style
        if p.startswith("*") and p.endswith("*") and p.count("*") == 2:
            # Italic pull-quote or tagline
            content = p.strip("*").strip()
            if content.startswith("The dwarf"):
                paragraphs.append((content, "pull_quote"))
            elif "watch carries forward" in content:
                paragraphs.append((content, "tagline"))
            else:
                paragraphs.append((content, "italic_phrase"))
        elif p.startswith("ASTRA-7 ·"):
            paragraphs.append((p, "byline"))
        elif "·" in p and ("Steam" in p or "GitHub" in p):
            paragraphs.append((p, "meta"))
        elif p.startswith("Free. Single-player."):
            paragraphs.append((p, "meta"))
        else:
            # Body — strip inline italic/bold markers for rendering
            cleaned = re.sub(r"\*\*?", "", p)
            paragraphs.append((cleaned, "body"))

    return paragraphs


# ============================================================
# Render front panel: hex + ASTRA-7 wordmark, centered
# ============================================================
def render_front(canvas):
    draw = ImageDraw.Draw(canvas)
    front_cx = FRONT_X0 + TRIM_W_PX // 2
    # Center vertically on the visible trim, not the full canvas
    front_cy = TRIM_TOP + TRIM_H_PX // 2

    # Wordmark sizing — proportional to trim, slightly larger than Kindle
    # since the visible trim is the print canvas (not the full Kindle 1600×2560)
    wordmark_size = int(TRIM_H_PX * 0.075)  # ~202 px
    wordmark_tracking = 0.02
    wordmark_font = font_semibold(wordmark_size)
    tw, th = measure_tracked(WORDMARK, wordmark_font, wordmark_tracking)

    hex_radius = int(th * 0.55)
    hex_diameter = hex_radius * 2
    gap = int(wordmark_size * 0.35)
    total_w = hex_diameter + gap + tw

    # Shift slightly right of pure center to clear the spine hinge area
    x_shift = 30
    x_start = front_cx - total_w // 2 + x_shift

    # Hexagon
    hex_cx = x_start + hex_radius
    hex_cy = front_cy
    draw_hexagon(draw, hex_cx, hex_cy, hex_radius, WHITE, stroke=6)

    # Wordmark
    wordmark_x = x_start + hex_diameter + gap
    asc, desc = wordmark_font.getmetrics()
    wordmark_y = front_cy - asc // 2 - desc // 4
    draw_tracked(draw, (wordmark_x, wordmark_y), WORDMARK, wordmark_font, wordmark_tracking, WHITE)

    print(f"  Front: hex r={hex_radius}px, wordmark {wordmark_size}px Inter SemiBold")


# ============================================================
# Render spine: vertical "THE LONG WATCH"
# ============================================================
def render_spine(canvas):
    # Build text horizontally on temp canvas (TRIM_H_PX wide, SPINE_W_PX tall),
    # then rotate -90° (clockwise) for top-to-bottom reading on spine.
    tmp_w = TRIM_H_PX
    tmp_h = SPINE_W_PX
    tmp = Image.new("RGB", (tmp_w, tmp_h), NAVY)
    tmp_draw = ImageDraw.Draw(tmp)

    # Auto-fit spine title — title length depends on text; shrink to fit if needed
    spine_title_size = int(SPINE_W_PX * 0.42)
    spine_title_tracking = 0.04
    spine_max_w = int(tmp_w * 0.85)  # 85% of spine length, leaving ornament room at ends
    while spine_title_size > 30:
        spine_title_font = font_semibold(spine_title_size)
        sw_t, sh_t = measure_tracked(SPINE_TITLE, spine_title_font, spine_title_tracking)
        if sw_t <= spine_max_w:
            break
        spine_title_size -= 2
    title_x = (tmp_w - sw_t) // 2
    title_y = (tmp_h - sh_t) // 2
    draw_tracked(tmp_draw, (title_x, title_y), SPINE_TITLE, spine_title_font, spine_title_tracking, WHITE)
    # Double-draw for spine readability at narrow widths
    draw_tracked(tmp_draw, (title_x + 1, title_y), SPINE_TITLE, spine_title_font, spine_title_tracking, WHITE)

    spine_rotated = tmp.rotate(-90, expand=True)
    canvas.paste(spine_rotated, (SPINE_X0, TRIM_TOP))

    print(f"  Spine: '{SPINE_TITLE}' vertical, {spine_title_size}px Inter SemiBold")


# ============================================================
# Render back panel: description text from back_cover.md
# ============================================================
def render_back(canvas):
    draw = ImageDraw.Draw(canvas)
    paragraphs = parse_back_cover()

    # Text area inside the back panel visible trim, with safe margin.
    # The SPINE side of the back panel is BACK_X1 (right edge of back in the wrap layout),
    # NOT BACK_X0. Hinge clearance goes on the spine side (right of back panel).
    text_left = BACK_X0 + SAFE_MARGIN_PX  # outer edge: standard safe margin
    text_right = BACK_X1 - SAFE_MARGIN_PX - SPINE_HINGE_PX  # spine side: extra clearance for binding
    text_top = TRIM_TOP + SAFE_MARGIN_PX
    text_bottom = TRIM_BOTTOM - SAFE_MARGIN_PX

    # ISBN barcode safe zone (KDP auto-overlay): bottom-right of visible trim
    # 2" × 1.2", inset ~0.25" from trim edges
    # We don't draw a placeholder, but we DO reserve the area (don't put text there)
    # In practice: stop body text ~1.6" from bottom on the right side, but
    # tagline/byline at very bottom that center across panel is fine.
    barcode_top_in = 1.4  # leave bottom 1.4" clear of body text on right side
    barcode_clearance_px = int(barcode_top_in * DPI)
    body_text_bottom = text_bottom - barcode_clearance_px

    text_w = text_right - text_left
    print(f"  Back text area: x=[{text_left},{text_right}] y=[{text_top},{text_bottom}]")
    print(f"  Body text bottom clearance: {barcode_top_in}\" for KDP ISBN auto-overlay")

    # Render paragraphs in sequence with style-appropriate typography
    y = text_top

    # Style settings
    pull_quote_size = int(TRIM_H_PX * 0.020)   # ~54 px
    body_size = int(TRIM_H_PX * 0.0155)        # ~42 px
    meta_size = int(TRIM_H_PX * 0.013)         # ~35 px
    tagline_size = int(TRIM_H_PX * 0.020)      # ~54 px
    byline_size = int(TRIM_H_PX * 0.012)       # ~32 px
    italic_phrase_size = int(TRIM_H_PX * 0.016)  # ~43 px

    def render_paragraph(text, style):
        nonlocal y
        if style == "pull_quote":
            font = font_medium(pull_quote_size)
            color = OFF_WHITE
            line_height = int(pull_quote_size * 1.35)
            margin_top = int(pull_quote_size * 0.5)
            margin_bottom = int(pull_quote_size * 1.0)
            align = "center"
        elif style == "body":
            font = font_regular(body_size)
            color = WHITE
            line_height = int(body_size * 1.45)
            margin_top = int(body_size * 0.6)
            margin_bottom = int(body_size * 0.3)
            align = "left"
        elif style == "tagline":
            font = font_semibold(tagline_size)
            color = OFF_WHITE
            line_height = int(tagline_size * 1.3)
            margin_top = int(tagline_size * 0.8)
            margin_bottom = int(tagline_size * 0.6)
            align = "center"
        elif style == "italic_phrase":
            font = font_medium(italic_phrase_size)
            color = OFF_WHITE
            line_height = int(italic_phrase_size * 1.35)
            margin_top = int(italic_phrase_size * 0.4)
            margin_bottom = int(italic_phrase_size * 0.4)
            align = "left"
        elif style == "meta":
            font = font_regular(meta_size)
            color = SOFT_WHITE
            line_height = int(meta_size * 1.4)
            margin_top = int(meta_size * 0.5)
            margin_bottom = int(meta_size * 0.2)
            align = "left"
        elif style == "byline":
            font = font_regular(byline_size)
            color = DIM_WHITE
            line_height = int(byline_size * 1.4)
            margin_top = int(byline_size * 1.5)
            margin_bottom = int(byline_size * 0.3)
            align = "center"
        else:
            font = font_regular(body_size)
            color = WHITE
            line_height = int(body_size * 1.45)
            margin_top = int(body_size * 0.5)
            margin_bottom = int(body_size * 0.3)
            align = "left"

        y += margin_top

        lines = wrap_text(text, font, text_w)
        for line in lines:
            line_bbox = font.getbbox(line)
            line_w = line_bbox[2] - line_bbox[0]
            if align == "center":
                lx = text_left + (text_w - line_w) // 2
            else:
                lx = text_left
            draw.text((lx, y), line, font=font, fill=color)
            y += line_height

        y += margin_bottom

    # Push body content down a bit from the top for breathing room
    y = text_top + int(TRIM_H_PX * 0.04)

    for text, style in paragraphs:
        render_paragraph(text, style)

    print(f"  Back: {len(paragraphs)} paragraphs rendered, final y={y}")


# ============================================================
# Main
# ============================================================
def make_wrap():
    print(f"\n=== KDP HARDCOVER WRAP (ASTRA-7 minimal design) ===")
    print(f"  Pages: {PAGES} (white paper)")
    print(f"  Spine: {SPINE_IN}\" ({SPINE_W_PX} px)")
    print(f"  Wrap dimensions: {WRAP_W_IN}\" x {WRAP_H_IN}\"")
    print(f"  Pixel canvas: {WRAP_W} x {WRAP_H}")
    print(f"  Turn-in: {WRAP_SIDE_IN}\" all sides ({WRAP_PX} px)")
    print(f"  Panels: back x=[{BACK_X0},{BACK_X1}], spine x=[{SPINE_X0},{SPINE_X1}], front x=[{FRONT_X0},{FRONT_X1}]")
    print(f"  Trim y=[{TRIM_TOP},{TRIM_BOTTOM}]")

    # Fill entire canvas with navy (turn-in areas + all panels)
    canvas = Image.new("RGB", (WRAP_W, WRAP_H), NAVY)

    render_back(canvas)
    render_spine(canvas)
    render_front(canvas)

    # Save outputs
    canvas.save(OUT_JPG, "JPEG", quality=92, optimize=True, dpi=(DPI, DPI))
    canvas.save(OUT_PDF, "PDF", resolution=float(DPI))

    sz_pdf = OUT_PDF.stat().st_size
    sz_jpg = OUT_JPG.stat().st_size
    print(f"\n  Output PDF: {OUT_PDF.name}  ({sz_pdf:,} bytes / {sz_pdf/1024/1024:.1f} MB)")
    print(f"  Output JPG: {OUT_JPG.name}  ({sz_jpg:,} bytes / {sz_jpg/1024/1024:.1f} MB)")
    print(f"  Dimensions: {WRAP_W}x{WRAP_H} px @ {DPI} DPI = {WRAP_W/DPI:.4f}\" x {WRAP_H/DPI:.4f}\"")
    print(f"  Verify at KDP Print Previewer. If rejected, derive new spine from KDP's stated dimension.")


if __name__ == "__main__":
    print("=== KDP HARDCOVER WRAP COMPOSITE — The Long Watch (ASTRA-7 minimal) ===")
    make_wrap()
    print("\nDone.\n")
