"""
Composite the KINDLE EBOOK COVER for The Long Watch.

Design: minimal — dark navy background with the ASTRA-7 logo + wordmark
centered. Nothing else, no other images.

  Background: dark navy #0D1B2A (matches the ASTRA-7 brand)
  Logo:       white hexagon outline (drawn programmatically)
  Wordmark:   "ASTRA-7" in Inter SemiBold, white

The book title and author appear inside the book (title page) but not on
the cover, per Bo's spec. Amazon shows the book title separately from the
cover thumbnail in its listing, so the cover identifies the SERIES, not
this specific volume.

KDP Kindle cover spec:
  - 1600 x 2560 pixels (1.6:1 ratio)
  - JPEG, sRGB
  - Max 50 MB
  - Front cover only (no spine, no back, no wrap)

Output:
  C:\\ASTRA-7\\book\\production\\outputs\\kindle\\The_Long_Watch_KINDLE_cover.jpg
"""

import math
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# ============================================================
# KINDLE TARGET
# ============================================================
TARGET_W = 1600
TARGET_H = 2560

# ============================================================
# COLORS (ASTRA-7 brand palette) — v2 uses the darker navy
# ============================================================
NAVY = (6, 14, 28)         # #060E1C — darker than v1's #0D1B2A
WHITE = (255, 255, 255)    # logo + wordmark
OFF_WHITE = (240, 240, 245)  # slight cool-white for printed feel

# ============================================================
# PATHS
# ============================================================
ROOT = Path(r"C:\ASTRA-7")
OUT_DIR = ROOT / "book" / "production" / "outputs" / "kindle"
OUT_DIR.mkdir(exist_ok=True, parents=True)
OUT_PATH = OUT_DIR / "The_Long_Watch_KINDLE_cover_v2.jpg"

# Font selection — Inter SemiBold is the closest installed match to the
# screenshot aesthetic (modern tech-brand bold sans).
WIN_FONTS = Path(r"C:\Windows\Fonts")
FONT_PRIMARY = WIN_FONTS / "Inter-SemiBold.ttf"
FONT_FALLBACK = WIN_FONTS / "arialbd.ttf"  # Arial Bold as ultimate fallback


# ============================================================
# Helpers
# ============================================================
def load_font(size, prefer_bold=True):
    if FONT_PRIMARY.exists():
        return ImageFont.truetype(str(FONT_PRIMARY), size=size)
    return ImageFont.truetype(str(FONT_FALLBACK), size=size)


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


def draw_hexagon(draw, cx, cy, radius, color, stroke=8):
    """Draw a regular hexagon outline centered at (cx, cy) with given radius."""
    pts = []
    for i in range(6):
        # Start at top, rotate clockwise
        angle = math.radians(60 * i - 90)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        pts.append((x, y))
    # Close the polygon
    pts.append(pts[0])
    # Draw thick stroke by drawing multiple offset lines
    for offset in range(stroke):
        d = offset - stroke // 2
        offset_pts = [(p[0] + d * 0.5, p[1] + d * 0.5) for p in pts]
        draw.line(offset_pts, fill=color, width=2)
    # Simpler approach: draw a polygon with explicit stroke
    draw.line(pts, fill=color, width=stroke, joint="curve")


# ============================================================
# Compose
# ============================================================
def make_kindle_cover():
    print(f"\n=== The Long Watch — Kindle Cover {TARGET_W}x{TARGET_H} (ASTRA-7 minimal) ===")

    canvas = Image.new("RGB", (TARGET_W, TARGET_H), NAVY)
    draw = ImageDraw.Draw(canvas)

    # ---- ASTRA-7 wordmark (logo + text, horizontal, centered) ----
    # The wordmark is THE design element. Center it both horizontally
    # and vertically on the canvas.

    # Wordmark text size — large but not so large it touches the trim
    wordmark_size = int(TARGET_H * 0.075)  # ~192 px
    wordmark_tracking = 0.02
    wordmark_text = "ASTRA-7"
    wordmark_font = load_font(wordmark_size, prefer_bold=True)
    tw, th = measure_tracked(wordmark_text, wordmark_font, wordmark_tracking)

    # Hexagon size — proportional to wordmark height (about 0.85x for visual balance)
    hex_radius = int(th * 0.55)
    hex_diameter = hex_radius * 2

    # Gap between hex and wordmark
    gap = int(wordmark_size * 0.35)

    # Total width of (hex + gap + wordmark)
    total_width = hex_diameter + gap + tw

    # Center horizontally
    x_start = (TARGET_W - total_width) // 2
    # Center vertically (visually slightly above center for better balance)
    y_center = int(TARGET_H * 0.50)

    # Hexagon
    hex_cx = x_start + hex_radius
    hex_cy = y_center
    draw_hexagon(draw, hex_cx, hex_cy, hex_radius, WHITE, stroke=6)

    # Wordmark
    wordmark_x = x_start + hex_diameter + gap
    asc, desc = wordmark_font.getmetrics()
    wordmark_y = y_center - asc // 2 - desc // 4
    draw_tracked(draw, (wordmark_x, wordmark_y), wordmark_text, wordmark_font, wordmark_tracking, WHITE)

    print(f"  Wordmark: {wordmark_size}px Inter SemiBold, tracked {wordmark_tracking}, {tw}px wide")
    print(f"  Hexagon: radius={hex_radius}px, stroke=6px")
    print(f"  Total wordmark width: {total_width}px, centered at canvas x={TARGET_W//2}")
    print(f"  Vertical position: y={y_center} (canvas center)")

    # ---- SAVE ----
    canvas.save(OUT_PATH, "JPEG", quality=94, optimize=True)
    sz = OUT_PATH.stat().st_size
    print(f"\n  Output: {OUT_PATH.name}")
    print(f"          {sz:,} bytes ({sz/1024:.0f} KB)")
    print(f"          {TARGET_W}x{TARGET_H} JPEG q=94")
    print(f"          KDP Kindle ready (1600x2560 spec, < 50 MB max)")


if __name__ == "__main__":
    make_kindle_cover()
    print("\nDone.\n")
