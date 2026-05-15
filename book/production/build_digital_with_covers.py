"""
Build the DIGITAL PDF edition of The Long Watch.

Source: the print interior PDF (already includes page numbers + running header).
Prepend: the Kindle front cover JPG as page 1.
Optional: a back-cover JPG as the final page (if available).

The result is a standalone digital PDF that can be distributed alongside the
Kindle ebook and the print editions. Reuses the print interior because:
  - It already has page numbers and running headers (digital-readable)
  - The mirror margins are subtle in single-page view
  - The recto-enforced blank pages add minor flutter but are acceptable

If a distinct digital interior is wanted later (no mirror margins, no recto
enforcement), see _reference_inside_the_region/generate_digital_docx.py for
the Python+python-docx pattern from Inside_The_Region.

Inputs:
  - C:\\ASTRA-7\\book\\production\\outputs\\kdp_print\\The_Long_Watch_PRINT_INTERIOR.pdf
  - C:\\ASTRA-7\\book\\production\\outputs\\kindle\\The_Long_Watch_KINDLE_cover.jpg
  - Optional: C:\\ASTRA-7\\book\\cover_art\\back_cover.png (if exists)

Output:
  - C:\\ASTRA-7\\book\\production\\outputs\\digital\\The_Long_Watch_DIGITAL.pdf
"""

from pathlib import Path
import io
import sys
import fitz  # PyMuPDF
from PIL import Image

ROOT = Path(r"C:\ASTRA-7")
SRC_PDF = ROOT / "book" / "production" / "outputs" / "kdp_print" / "The_Long_Watch_PRINT_INTERIOR.pdf"
FRONT_COVER_JPG = ROOT / "book" / "production" / "outputs" / "kindle" / "The_Long_Watch_KINDLE_cover.jpg"
BACK_COVER_IMG = ROOT / "book" / "cover_art" / "back_cover.png"

OUT_DIR = ROOT / "book" / "production" / "outputs" / "digital"
OUT_DIR.mkdir(exist_ok=True, parents=True)
OUT_PDF = OUT_DIR / "The_Long_Watch_DIGITAL.pdf"

DEEP_NAVY = (8, 18, 32)  # matches print cover background


def render_cover_page_to_jpeg(img_path: Path, page_w_pt: float, page_h_pt: float, dpi: int = 200) -> bytes:
    """Build a JPEG that exactly matches the page size at `dpi`, with the source
    image scale-to-fit centered inside, letterboxed in DEEP_NAVY. Returns JPEG
    bytes ready to be embedded as a full-page image."""
    page_w_px = int(round(page_w_pt / 72 * dpi))
    page_h_px = int(round(page_h_pt / 72 * dpi))

    src = Image.open(img_path).convert("RGB")
    sw, sh = src.size
    scale = min(page_w_px / sw, page_h_px / sh)
    nw = int(sw * scale)
    nh = int(sh * scale)
    src_scaled = src.resize((nw, nh), Image.LANCZOS)

    canvas = Image.new("RGB", (page_w_px, page_h_px), DEEP_NAVY)
    canvas.paste(src_scaled, ((page_w_px - nw) // 2, (page_h_px - nh) // 2))

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=88, optimize=True, dpi=(dpi, dpi))
    return buf.getvalue()


def main():
    if not SRC_PDF.exists():
        print(f"ERROR: print interior PDF missing at {SRC_PDF}")
        print("Run the print interior pipeline first:")
        print("  1. node generate_book_kdp_hardcover.js")
        print("  2. python update_hardcover_and_count.py")
        sys.exit(1)
    if not FRONT_COVER_JPG.exists():
        print(f"ERROR: front cover JPG missing at {FRONT_COVER_JPG}")
        print("Run composite_cover_kindle.py first.")
        sys.exit(1)

    print(f"Source content: {SRC_PDF.name}")
    src = fitz.open(str(SRC_PDF))
    n_src = len(src)
    p0 = src[0]
    page_w_pt = p0.rect.width
    page_h_pt = p0.rect.height
    print(f"  Pages: {n_src}")
    print(f"  Page size: {page_w_pt:.2f} x {page_h_pt:.2f} pt  ({page_w_pt/72:.4f}\" x {page_h_pt/72:.4f}\")")

    out = fitz.open()

    # Page 1: front cover
    print(f"\nAdding page 1: front cover ({FRONT_COVER_JPG.name})")
    front_jpeg = render_cover_page_to_jpeg(FRONT_COVER_JPG, page_w_pt, page_h_pt)
    page = out.new_page(width=page_w_pt, height=page_h_pt)
    page.insert_image(page.rect, stream=front_jpeg)

    # Pages 2..(N+1): append entire source PDF as-is
    print(f"Appending {n_src} pages from print interior PDF")
    out.insert_pdf(src)

    # Optional: back cover as final page (if back_cover.png exists)
    if BACK_COVER_IMG.exists():
        print(f"\nAdding final page: back cover ({BACK_COVER_IMG.name})")
        back_jpeg = render_cover_page_to_jpeg(BACK_COVER_IMG, page_w_pt, page_h_pt)
        page = out.new_page(width=page_w_pt, height=page_h_pt)
        page.insert_image(page.rect, stream=back_jpeg)
    else:
        print(f"\n  (Optional back cover at {BACK_COVER_IMG.name} not present; skipping.)")

    print(f"\nWriting {OUT_PDF.name}")
    out.save(str(OUT_PDF), garbage=4, deflate=True)
    out.close()
    src.close()

    sz = OUT_PDF.stat().st_size
    final = fitz.open(str(OUT_PDF))
    print(f"  Size: {sz:,} bytes ({sz/1024/1024:.2f} MB)")
    print(f"  Total pages: {len(final)}")
    final.close()


if __name__ == "__main__":
    main()
    print("\nDone.")
