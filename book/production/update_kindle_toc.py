"""
Update the auto-TOC field in the Kindle DOCX via Word COM.
Required because docx@9 emits the TOC placeholder but only Word can populate it.

After this runs, the DOCX is ready for direct KDP Kindle upload.
"""

import sys
from pathlib import Path
import win32com.client

DOCX_PATH = Path(r"C:\ASTRA-7\book\production\outputs\kindle\The_Long_Watch_KINDLE.docx")

if not DOCX_PATH.exists():
    print(f"ERROR: {DOCX_PATH} does not exist. Run generate_kindle.js first.")
    sys.exit(1)

print(f"Opening {DOCX_PATH.name} in Word...")
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0

try:
    doc = word.Documents.Open(str(DOCX_PATH.resolve()))

    # Update all TOC fields
    toc_count = doc.TablesOfContents.Count
    print(f"  TOC fields found: {toc_count}")
    for i in range(toc_count):
        toc = doc.TablesOfContents(i + 1)
        toc.Update()
        print(f"  TOC {i+1}: updated")

    # Repaginate (Word will compute everything fresh)
    doc.Repaginate()

    # Save in place
    doc.Save()
    print(f"  Saved {DOCX_PATH.name}")

    # Word stats just for the report (Kindle reflows ignores them)
    pages = doc.ComputeStatistics(2)  # wdStatisticPages
    words = doc.ComputeStatistics(0)  # wdStatisticWords
    print(f"  Word stats: {words:,} words / {pages} pages (informational; Kindle ignores pages)")

    doc.Close(SaveChanges=False)
finally:
    word.Quit()

print(f"\nDone. {DOCX_PATH.name} ready for KDP Kindle upload.")
