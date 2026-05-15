"""
Post-process the print interior DOCX after generate_book_kdp_hardcover.js:
  1. Open in Word via COM
  2. Update all TOC fields (Word fills in cycle titles + page numbers)
  3. Repaginate twice (TOC update shifts page count slightly the first pass)
  4. Save in place
  5. Save as PDF (FileFormat=17 = wdFormatPDF)
  6. Report page count and compute spine math for BOTH paperback and hardcover

Same interior DOCX is used for both KDP paperback and KDP hardcover per the
Inside_The_Region addendum 8 strategy. Spine math differs by format because
hardcover adds boards.

Spine formulas (empirical, post Inside_The_Region v3 KDP acceptance):
  Paperback (white paper): pages * 0.002252                 [no board addition]
  Hardcover (white paper): pages * 0.0025 + 0.241           [boards included]

Critical: these are CURRENT, not the older Titanic-era 0.002252 + 0.302
formula. KDP's hardcover spec has shifted. Use these and verify against KDP
Print Previewer; if rejected, derive new spine from KDP's stated dimension
in the error message.
"""

from pathlib import Path
import sys
import win32com.client

DOCX_PATH = Path(r"C:\ASTRA-7\book\production\outputs\kdp_print\The_Long_Watch_PRINT_INTERIOR.docx")
PDF_PATH  = Path(r"C:\ASTRA-7\book\production\outputs\kdp_print\The_Long_Watch_PRINT_INTERIOR.pdf")

if not DOCX_PATH.exists():
    print(f"ERROR: {DOCX_PATH} missing. Run generate_book_kdp_hardcover.js first.")
    sys.exit(1)

print(f"Opening {DOCX_PATH.name} in Word...")
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0

try:
    doc = word.Documents.Open(str(DOCX_PATH.resolve()))

    # Update TOC fields
    toc_count = doc.TablesOfContents.Count
    print(f"  TOC fields: {toc_count}")
    for i in range(toc_count):
        doc.TablesOfContents(i + 1).Update()
        print(f"  TOC {i+1}: updated")

    # Repaginate twice (TOC update can shift the count)
    doc.Repaginate()
    doc.Repaginate()

    # Save in place
    doc.Save()

    # Save as PDF
    doc.SaveAs(str(PDF_PATH.resolve()), FileFormat=17)
    print(f"  Saved {PDF_PATH.name}")

    # Stats
    pages = doc.ComputeStatistics(2)  # wdStatisticPages
    words = doc.ComputeStatistics(0)  # wdStatisticWords
    print()
    print("=== Print interior stats ===")
    print(f"  Words: {words:,}")
    print(f"  Pages: {pages}")
    print(f"  Multiple-of-2 (KDP req): {'YES' if pages % 2 == 0 else 'NO — fix trailing blank in generator'}")

    # Spine math — paperback
    SPINE_PER_PAGE_PAPERBACK = 0.002252  # No board addition
    spine_pb = pages * SPINE_PER_PAGE_PAPERBACK
    wrap_pb_w = 12 + spine_pb + 0.25  # 6 (back) + 6 (front) + spine + 0.125 bleed * 2
    wrap_pb_h = 9 + 0.25  # 9 + 0.125 bleed * 2
    print()
    print("=== KDP PAPERBACK cover wrap dimensions (white paper) ===")
    print(f"  Spine width: {spine_pb:.4f}\" ({pages} * 0.002252)")
    print(f"  Wrap width:  {wrap_pb_w:.4f}\" (12 + spine + 0.25 bleed)")
    print(f"  Wrap height: {wrap_pb_h:.4f}\" (9.25)")

    # Spine math — hardcover (empirical, post Inside_The_Region v3 KDP acceptance)
    SPINE_PER_PAGE_HARDCOVER = 0.0025
    SPINE_BOARDS_HARDCOVER = 0.241
    spine_hc = pages * SPINE_PER_PAGE_HARDCOVER + SPINE_BOARDS_HARDCOVER
    wrap_hc_w = 12 + spine_hc + 1.416  # 12 + spine + 0.708 turn-in * 2
    wrap_hc_h = 10.417  # KDP validator-rounded; arithmetic = 9 + 0.708*2 = 10.416
    print()
    print("=== KDP HARDCOVER cover wrap dimensions (white paper) ===")
    print(f"  Spine width: {spine_hc:.4f}\" ({pages} * 0.0025 + 0.241)")
    print(f"  Wrap width:  {wrap_hc_w:.4f}\" (12 + spine + 1.416 turn-in)")
    print(f"  Wrap height: {wrap_hc_h:.4f}\" (KDP validator-rounded)")
    print()
    print("Pass these page count and wrap dimensions to:")
    print("  composite_cover_kdp_paperback.py (paperback)")
    print("  composite_cover_kdp_hardcover.py (hardcover)")
    print(f"  PAGES = {pages}")

    doc.Close(SaveChanges=False)
finally:
    word.Quit()
