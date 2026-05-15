"""
Composite the SINGLE-WRAP cover for Amazon KDP PAPERBACK.

The Long Watch — 6x9 paperback, white paper, ASTRA-7 minimal design.

DESIGN: matches hardcover (ASTRA-7 wordmark front, description on back).
Differences from hardcover wrap:
  - 0.125" bleed (vs 0.708" hardcover turn-in)
  - Spine has NO board offset (pages * 0.002252 only, not + 0.241)
  - Smaller spine; same body interior is reused

Spine formula (KDP paperback, white paper, no boards):
  Spine = pages * 0.002252

Inputs (configurable below):
  - PAGES: from update_hardcover_and_count.py output
  - book/back_cover.md: source text for back panel
  - book/manuscript/back_02_colophon.md: same as hardcover

Output:
  C:\\ASTRA-7\\book\\production\\outputs\\kdp_print\\cover_wrap_paperback.pdf
  C:\\ASTRA-7\\book\\production\\outputs\\kdp_print\\cover_wrap_paperback.jpg (preview)
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

# Page count drives spine. Update after running update_hardcover_and_count.py
PAGES = 186

SPINE_PER_PAGE_PAPERBACK = 0.002252  # No board offset
SPINE_IN = round(PAGES * SPINE_PER_PAGE_PAPERBACK, 4)

# Bleed
BLEED_IN = 0.125

# Total wrap dimensions
WRAP_W_IN = round(TRIM_W_IN * 2 + SPINE_IN + BLEED_IN * 2, 4)
WRAP_H_IN = round(TRIM_H_IN + BLEED_IN * 2, 4)

# Pixel canvas
WRAP_W = round(WRAP_W_IN * DPI)
WRAP_H = round(WRAP_H_IN * DPI)

# Panel pixel widths
BLEED_PX = round(BLEED_IN * DPI)
TRIM_W_PX = round(TRIM_W_IN * DPI)
TRIM_H_PX = round(TRIM_H_IN * DPI)
SPINE_W_PX = WRAP_W - 2 * BLEED_PX - 2 * TRIM_W_PX

# Panel x-coordinates
BACK_X0 = BLEED_PX
BACK_X1 = BACK_X0 + TRIM_W_PX
SPINE_X0 = BACK_X1
SPINE_X1 = SPINE_X0 + SPINE_W_PX
FRONT_X0 = SPINE_X1
FRONT_X1 = FRONT_X0 + TRIM_W_PX

# Trim y-coordinates
TRIM_TOP = BLEED_PX
TRIM_BOTTOM = WRAP_H - BLEED_PX

# Safe margins (KDP paperback)
SAFE_MARGIN_IN = 0.5
SAFE_MARGIN_PX = round(SAFE_MARGIN_IN * DPI)
# Spine hinge clearance is smaller on paperback (no boards)
SPINE_HINGE_IN = 0.25
SPINE_HINGE_PX = round(SPINE_HINGE_IN * DPI)

# Colors (ASTRA-7 brand)
NAVY = (13, 27, 42)
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
OUT_PDF = OUT_DIR / "cover_wrap_paperback.pdf"
OUT_JPG = OUT_DIR / "cover_wrap_paperback.jpg"

# Metadata
WORDMARK = "ASTRA-7"
SPINE_TITLE = "ASTRA-7: THE LONG WATCH"


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
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 90)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        pts.append((x, y))
    pts.append(pts[0])
    draw.line(pts, fill=color, width=stroke, joint="curve")


def wrap_text(text, font, max_width):
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
# Parse back_cover.md
# ============================================================
def parse_back_cover():
    md = BACK_COVER_MD.read_text(encoding="utf-8")
    parts = md.split("---", 1)
    body = parts[1] if len(parts) > 1 else parts[0]
    raw_paragraphs = re.split(r"\n\s*\n", body.strip())
    paragraphs = []
    for raw in raw_paragraphs:
        p = raw.strip()
        if not p:
            continue
        p = p.replace("\n", " ").strip()
        if p.startswith("*") and p.endswith("*") and p.count("*") == 2:
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
            cleaned = re.sub(r"\*\*?", "", p)
            paragraphs.append((cleaned, "body"))
    return paragraphs


# ============================================================
# Render front panel: hex + ASTRA-7 wordmark
# ============================================================
def render_front(canvas):
    draw = ImageDraw.Draw(canvas)
    front_cx = FRONT_X0 + TRIM_W_PX // 2
    front_cy = TRIM_TOP + TRIM_H_PX // 2

    wordmark_size = int(TRIM_H_PX * 0.075)
    wordmark_tracking = 0.02
    wordmark_font = font_semibold(wordmark_size)
    tw, th = measure_tracked(WORDMARK, wordmark_font, wordmark_tracking)

    hex_radius = int(th * 0.55)
    hex_diameter = hex_radius * 2
    gap = int(wordmark_size * 0.35)
    total_w = hex_diameter + gap + tw

    # Paperback hinge consumes less of the front panel than hardcover (no board fold)
    x_shift = 20
    x_start = front_cx - total_w // 2 + x_shift

    hex_cx = x_start + hex_radius
    hex_cy = front_cy
    draw_hexagon(draw, hex_cx, hex_cy, hex_radius, WHITE, stroke=6)

    wordmark_x = x_start + hex_diameter + gap
    asc, desc = wordmark_font.getmetrics()
    wordmark_y = front_cy - asc // 2 - desc // 4
    draw_tracked(draw, (wordmark_x, wordmark_y), WORDMARK, wordmark_font, wordmark_tracking, WHITE)

    print(f"  Front: hex r={hex_radius}px, wordmark {wordmark_size}px Inter SemiBold")


# ============================================================
# Render spine: vertical title
# ============================================================
def render_spine(canvas):
    tmp_w = TRIM_H_PX
    tmp_h = SPINE_W_PX
    tmp = Image.new("RGB", (tmp_w, tmp_h), NAVY)
    tmp_draw = ImageDraw.Draw(tmp)

    spine_title_size = int(SPINE_W_PX * 0.40)
    spine_title_tracking = 0.04
    spine_max_w = int(tmp_w * 0.85)
    while spine_title_size > 22:
        spine_title_font = font_semibold(spine_title_size)
        sw_t, sh_t = measure_tracked(SPINE_TITLE, spine_title_font, spine_title_tracking)
        if sw_t <= spine_max_w:
            break
        spine_title_size -= 2
    title_x = (tmp_w - sw_t) // 2
    title_y = (tmp_h - sh_t) // 2
    draw_tracked(tmp_draw, (title_x, title_y), SPINE_TITLE, spine_title_font, spine_title_tracking, WHITE)
    draw_tracked(tmp_draw, (title_x + 1, title_y), SPINE_TITLE, spine_title_font, spine_title_tracking, WHITE)

    spine_rotated = tmp.rotate(-90, expand=True)
    canvas.paste(spine_rotated, (SPINE_X0, TRIM_TOP))

    print(f"  Spine: '{SPINE_TITLE}' vertical, {spine_title_size}px Inter SemiBold")


# ============================================================
# Render back panel: description text
# ============================================================
def render_back(canvas):
    draw = ImageDraw.Draw(canvas)
    paragraphs = parse_back_cover()

    text_left = BACK_X0 + SAFE_MARGIN_PX
    text_right = BACK_X1 - SAFE_MARGIN_PX - SPINE_HINGE_PX
    text_top = TRIM_TOP + SAFE_MARGIN_PX
    text_bottom = TRIM_BOTTOM - SAFE_MARGIN_PX

    # Reserve bottom 1.2" for KDP ISBN barcode auto-overlay
    barcode_top_in = 1.2
    barcode_clearance_px = int(barcode_top_in * DPI)
    body_text_bottom = text_bottom - barcode_clearance_px

    text_w = text_right - text_left

    pull_quote_size = int(TRIM_H_PX * 0.020)
    body_size = int(TRIM_H_PX * 0.0155)
    meta_size = int(TRIM_H_PX * 0.013)
    tagline_size = int(TRIM_H_PX * 0.020)
    byline_size = int(TRIM_H_PX * 0.012)
    italic_phrase_size = int(TRIM_H_PX * 0.016)

    y = text_top + int(TRIM_H_PX * 0.04)

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

    for text, style in paragraphs:
        render_paragraph(text, style)

    print(f"  Back: {len(paragraphs)} paragraphs rendered, text area x=[{text_left},{text_right}] y=[{text_top},{text_bottom}]")


# ============================================================
# Main
# ============================================================
def make_wrap():
    print(f"\n=== KDP PAPERBACK WRAP (ASTRA-7 minimal design) ===")
    print(f"  Pages: {PAGES} (white paper)")
    print(f"  Spine: {SPINE_IN}\" ({SPINE_W_PX} px) — NO board offset")
    print(f"  Wrap dimensions: {WRAP_W_IN}\" x {WRAP_H_IN}\"")
    print(f"  Pixel canvas: {WRAP_W} x {WRAP_H}")
    print(f"  Bleed: {BLEED_IN}\" all sides ({BLEED_PX} px)")
    print(f"  Panels: back x=[{BACK_X0},{BACK_X1}], spine x=[{SPINE_X0},{SPINE_X1}], front x=[{FRONT_X0},{FRONT_X1}]")

    canvas = Image.new("RGB", (WRAP_W, WRAP_H), NAVY)
    render_back(canvas)
    render_spine(canvas)
    render_front(canvas)

    canvas.save(OUT_JPG, "JPEG", quality=92, optimize=True, dpi=(DPI, DPI))
    canvas.save(OUT_PDF, "PDF", resolution=float(DPI))

    sz_pdf = OUT_PDF.stat().st_size
    sz_jpg = OUT_JPG.stat().st_size
    print(f"\n  Output PDF: {OUT_PDF.name}  ({sz_pdf:,} bytes / {sz_pdf/1024/1024:.1f} MB)")
    print(f"  Output JPG: {OUT_JPG.name}  ({sz_jpg:,} bytes / {sz_jpg/1024/1024:.1f} MB)")
    print(f"  Dimensions: {WRAP_W}x{WRAP_H} px @ {DPI} DPI = {WRAP_W/DPI:.4f}\" x {WRAP_H/DPI:.4f}\"")
    print(f"  KDP paperback target: ~{WRAP_W_IN}\" x {WRAP_H_IN}\"")


if __name__ == "__main__":
    print("=== KDP PAPERBACK WRAP COMPOSITE — The Long Watch (ASTRA-7 minimal) ===")
    make_wrap()
    print("\nDone.\n")
