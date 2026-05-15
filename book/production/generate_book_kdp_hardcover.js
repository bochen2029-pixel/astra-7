const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, PageBreak,
  HeadingLevel, TableOfContents, StyleLevel,
  SectionType, Header, Footer, PageNumber,
} = require("docx");
const JSZip = require("jszip");

// ============================================================
// KDP PRINT INTERIOR — The Long Watch
// (Same interior used for both KDP HARDCOVER and KDP PAPERBACK
// per Inside_The_Region addendum 8: byte-for-byte reuse.)
//
// 6" x 9" trim, mirror margins, recto-enforced chapter starts,
// page numbers in footer, running header with book title,
// trailing EVEN_PAGE blank for even total page count.
//
// Simplified from Inside_The_Region's generator. The Long Watch
// has NO math, code blocks, tables, bullets, numbered lists, or
// blockquotes — only prose paragraphs, italic/bold inline, and
// section-break dots ("· · ·").
//
// Section structure:
//   1. Front matter (half-title, title page, copyright, dedication,
//      epigraph) — loaded from front_NN_*.md files. No headers,
//      no page numbers.
//   2. Contents (auto-TOC) — no headers, no page numbers.
//   3. Body — one section per cycle file. ODD_PAGE forces recto.
//      Each cycle's H1 ("Cycle One", "Cycle Two", ...) is generated
//      by the script from the cycle number, NOT from the file content.
//      Running header "THE LONG WATCH" + page numbers (start at 1).
//   4. Back matter (afterword, colophon, acknowledgments, about the
//      author, print colophon) — loaded from back_NN_*.md files.
//      Each back matter file's content is rendered as a section.
//   5. Trailing EVEN_PAGE blank — guarantees even total page count
//      for KDP. Empty headers/footers required (see below).
//
// Mirror margins injected post-Packer via JSZip into word/settings.xml
// (docx@9 silently drops the per-section mirror flag).
//
// EMPTY HEADERS/FOOTERS REQUIRED on every section that should be
// blank-of-headers (front matter, TOC, back matter intro pages,
// trailing blank). Without explicit empty Header/Footer objects,
// Word inherits from the previous section and renders the running
// header + page number on what should be blank — KDP rejects as
// "text outside margins". See Inside_The_Region addendum 7.
// ============================================================

const FONT = "Georgia";
const TITLE_FONT = "Georgia";
const BODY_COLOR = "1A1A1A";
const BODY_SIZE = 22;       // 11pt
const BODY_LINE = 320;      // ~1.35x

// Book metadata
const BOOK_TITLE = "ASTRA-7: THE LONG WATCH";
const AUTHOR_NAME = "BO CHEN";

// Cycle number-to-word for H1 chapter titles
const CYCLE_WORDS = [
  null, "One", "Two", "Three", "Four", "Five", "Six", "Seven",
  "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen",
];

// Page: 6 × 9 in DXA (1 inch = 1440 DXA)
const PAGE_W = 8640;
const PAGE_H = 12960;

// Margins (validated against Inside_The_Region v4 KDP acceptance for 426pp)
const MARGIN_TOP = 720;       // 0.5"
const MARGIN_BOTTOM = 900;    // 0.625"
const MARGIN_GUTTER = 1260;   // 0.875" inside/spine
const MARGIN_OUTSIDE = 720;   // 0.5" outside

// Paths
const SRC_DIR = "C:\\ASTRA-7\\book\\manuscript";
const OUT_DIR = "C:\\ASTRA-7\\book\\production\\outputs\\kdp_print";
const OUT_PATH = path.join(OUT_DIR, "The_Long_Watch_PRINT_INTERIOR.docx");

// ============================================================
// Inline run builder — bold, italic only (no math, no code)
// ============================================================
function buildInlineRuns(text, baseOpts) {
  const runs = [];
  const boldParts = text.split(/(\*\*[^*]+\*\*)/g);
  for (const boldPart of boldParts) {
    if (boldPart.startsWith("**") && boldPart.endsWith("**") && boldPart.length > 4) {
      runs.push(new TextRun({ ...baseOpts, text: boldPart.slice(2, -2), bold: true }));
      continue;
    }
    if (boldPart.length === 0) continue;
    const italicParts = boldPart.split(/(\*[^*]+\*)/g);
    for (const part of italicParts) {
      if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
        runs.push(new TextRun({ ...baseOpts, text: part.slice(1, -1), italics: true }));
      } else if (part.length > 0) {
        runs.push(new TextRun({ ...baseOpts, text: part }));
      }
    }
  }
  return runs;
}

function createBodyParagraph(text, opts = {}) {
  const runs = buildInlineRuns(text, { font: FONT, size: BODY_SIZE, color: BODY_COLOR });
  return new Paragraph({
    spacing: { after: 120, line: BODY_LINE, lineRule: "atLeast" },
    indent: { firstLine: 360 },
    alignment: opts.alignment || AlignmentType.JUSTIFIED,
    children: runs,
  });
}

function createCenteredParagraph(text, opts = {}) {
  const runs = buildInlineRuns(text, {
    font: FONT,
    size: opts.size || BODY_SIZE,
    color: opts.color || BODY_COLOR,
    italics: opts.italics || false,
  });
  return new Paragraph({
    spacing: { after: opts.spacingAfter || 120, line: BODY_LINE, lineRule: "atLeast" },
    alignment: AlignmentType.CENTER,
    children: runs,
  });
}

function createH1(title, withPageBreak) {
  const out = [];
  if (withPageBreak) out.push(new Paragraph({ children: [new PageBreak()] }));
  out.push(new Paragraph({ spacing: { before: 1200, after: 200 } }));
  out.push(new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 200, after: 320 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: title, font: FONT, size: 28, color: BODY_COLOR, characterSpacing: 40, bold: true,
    })],
  }));
  out.push(new Paragraph({
    spacing: { before: 80, after: 480 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "\u2726", font: "Segoe UI Symbol", size: 20, color: "999999" })],
  }));
  return out;
}

function createSectionBreak() {
  return new Paragraph({
    spacing: { before: 240, after: 240 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "\u00B7  \u00B7  \u00B7", font: "Segoe UI Symbol", size: 16, color: "999999" })],
  });
}

function createBlankLineParagraph() {
  // For cycle 14's half-page white space and any intentional blank-line
  // clusters in the manuscript. Each consecutive blank line in the source
  // becomes one of these.
  return new Paragraph({
    spacing: { after: 0, line: 240, lineRule: "atLeast" },
    children: [new TextRun({ text: "", font: FONT, size: BODY_SIZE })],
  });
}

function pushDownEmptyParagraphs(count) {
  // Returns an array of `count` empty paragraphs used to physically push
  // content down on a page. Used in front-matter where `spacing.before`
  // after a PageBreak is unreliable in Word. Each paragraph is ~14pt tall
  // at default leading, so 5 paragraphs ≈ 1 inch of vertical space.
  const out = [];
  for (let i = 0; i < count; i++) {
    out.push(new Paragraph({
      spacing: { after: 0, line: 280, lineRule: "atLeast" },
      children: [new TextRun({ text: " ", font: FONT, size: BODY_SIZE })],
    }));
  }
  return out;
}

// ============================================================
// Markdown parser (simplified for The Long Watch)
//
// Handles ONLY:
//   - H1 (# Title)
//   - Body paragraphs (with **bold** and *italic*)
//   - Section breaks (· · · exact)
//   - Blank lines (preserved as empty paragraphs)
//
// opts.skipFirstH1PageBreak: omit the leading PageBreak on the first H1
//   in this chunk, since the section's ODD_PAGE break handles page advance.
// opts.preserveBlankLines: if true, emit one empty paragraph per blank line
//   (used for cycle 14's half-page white space). Default false: skip blanks.
// opts.centerParagraphs: if true, body paragraphs are centered (front matter).
// ============================================================
function parseMarkdown(text, opts = {}) {
  const lines = text.split("\n");
  const out = [];
  let firstH1Handled = false;
  const skipFirstH1PageBreak = opts.skipFirstH1PageBreak === true;
  const preserveBlankLines = opts.preserveBlankLines === true;
  const centerParagraphs = opts.centerParagraphs === true;

  let i = 0;

  while (i < lines.length) {
    const raw = lines[i];
    const line = raw.replace(/\s+$/, "");
    const stripped = line.trim();

    // Blank line
    if (stripped === "") {
      if (preserveBlankLines) out.push(createBlankLineParagraph());
      i++;
      continue;
    }

    // H1
    const h1Match = stripped.match(/^#\s+(.+)$/);
    if (h1Match && !stripped.startsWith("##")) {
      const title = h1Match[1].trim();
      const withPageBreak = !(skipFirstH1PageBreak && !firstH1Handled);
      out.push(...createH1(title, withPageBreak));
      firstH1Handled = true;
      i++;
      continue;
    }

    // Section break — three middle dots (with single or double spaces)
    if (stripped === "\u00B7 \u00B7 \u00B7" || stripped === "\u00B7  \u00B7  \u00B7") {
      out.push(createSectionBreak());
      i++;
      continue;
    }

    // Body paragraph — collect consecutive non-blank, non-special lines
    let paraLines = [stripped];
    i++;
    while (i < lines.length && lines[i].trim().length > 0) {
      const next = lines[i].trim();
      if (/^#{1,6}\s/.test(next)) break;
      if (next === "\u00B7 \u00B7 \u00B7" || next === "\u00B7  \u00B7  \u00B7") break;
      paraLines.push(next);
      i++;
    }
    const joined = paraLines.join(" ");
    if (centerParagraphs) {
      out.push(createCenteredParagraph(joined));
    } else {
      out.push(createBodyParagraph(joined));
    }
  }
  return out;
}

// ============================================================
// Cycle file discovery and ordering
// ============================================================
function discoverFiles(prefix) {
  // Returns alphabetically sorted list of files matching `${prefix}_*.md`
  // in SRC_DIR (e.g., prefix="front" → ["front_01_half_title.md", ...]).
  if (!fs.existsSync(SRC_DIR)) return [];
  return fs.readdirSync(SRC_DIR)
    .filter(f => f.startsWith(`${prefix}_`) && f.endsWith(".md"))
    .sort();
}

function discoverCycleFiles() {
  // Returns cycle_NN_*.md files in numeric order (cycle_01_* through cycle_14_*).
  return fs.readdirSync(SRC_DIR)
    .filter(f => /^cycle_\d{2}_.+\.md$/.test(f))
    .sort();
}

function cycleNumberFromFilename(filename) {
  const m = filename.match(/^cycle_(\d{2})_/);
  return m ? parseInt(m[1], 10) : null;
}

// ============================================================
// Front matter loader
//
// Loads front_NN_*.md files in order. Each file becomes its own page
// (PageBreak between files). Content rendered with centered alignment.
//
// Convention:
//   - front_01_half_title.md       → large title typography
//   - front_02_title_page.md       → title + author + imprint
//   - front_03_copyright.md        → small text, centered
//   - front_04_dedication.md       → italic centered (optional)
//   - front_05_epigraph.md         → italic centered + attribution
//
// All rendered as centered paragraphs with appropriate spacing.
// Files starting with [TBD or [OPTIONAL prefix in their content are
// rendered verbatim (the stubs); fill them in to control appearance.
// ============================================================
function buildFrontMatter() {
  const fm = [];
  const files = discoverFiles("front");
  let first = true;

  // Push-down values per file (number of empty paragraphs to insert before
  // content). Each empty paragraph is ~14pt high; 5 ≈ 1 inch of pushdown.
  // The pushdown approach is more reliable than `spacing.before` after a
  // PageBreak in Word.
  const PUSHDOWN = {
    half_title:  15,  // ~3"  — title centered on page
    title_page:  12,  // ~2.4" — title centered, leaves room for author/imprint
    copyright:   18,  // ~3.6" — copyright pushed toward bottom-mid
    dedication:  18,  // ~3.6" — dedication near center
    epigraph:    15,  // ~3"  — epigraph mid-upper
  };

  for (const filename of files) {
    if (!first) fm.push(new Paragraph({ children: [new PageBreak()] }));
    first = false;

    // Push content down before rendering (avoid Word ignoring spacing.before
    // immediately after a PageBreak)
    let pushdown = 12;
    for (const key of Object.keys(PUSHDOWN)) {
      if (filename.includes(key)) { pushdown = PUSHDOWN[key]; break; }
    }
    fm.push(...pushDownEmptyParagraphs(pushdown));

    const md = fs.readFileSync(path.join(SRC_DIR, filename), "utf8");

    // Custom rendering by filename
    if (filename.includes("half_title")) {
      // Large title-only page
      const title = md.trim();
      fm.push(new Paragraph({
        spacing: { before: 0, after: 200 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({
          text: title, font: TITLE_FONT, size: 32, color: BODY_COLOR, characterSpacing: 80, bold: true,
        })],
      }));
    } else if (filename.includes("title_page")) {
      // Title + author + imprint. Filter placeholder lines.
      const lines = md.split("\n").map(l => l.trim()).filter(l => l && !l.startsWith("["));
      if (lines.length > 0) {
        // First line: title (the full "ASTRA-7: The Long Watch")
        fm.push(new Paragraph({
          spacing: { before: 0, after: 200 },
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: lines[0], font: TITLE_FONT, size: 40, color: BODY_COLOR, characterSpacing: 60, bold: true,
          })],
        }));
        fm.push(new Paragraph({
          spacing: { before: 200, after: 200 },
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "\u2726", font: "Segoe UI Symbol", size: 22, color: "999999" })],
        }));
        // Remaining lines: author (line 1), imprint (line 2+)
        for (let i = 1; i < lines.length; i++) {
          fm.push(new Paragraph({
            spacing: { before: i === 1 ? 600 : 240, after: 60 },
            alignment: AlignmentType.CENTER,
            children: [new TextRun({
              text: lines[i],
              font: TITLE_FONT,
              size: i === 1 ? 24 : 16,
              color: i === 1 ? BODY_COLOR : "777777",
              characterSpacing: i === 1 ? 60 : 30,
              italics: i > 1,
            })],
          }));
        }
      }
    } else if (filename.includes("copyright")) {
      // Centered small text, paragraph-by-paragraph
      const paras = md.split(/\n\s*\n/).map(p => p.trim()).filter(p => p && !p.startsWith("["));
      for (const para of paras) {
        fm.push(new Paragraph({
          spacing: { before: 100, after: 100 },
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: para.replace(/\n/g, " "),
            font: FONT, size: 16, color: "555555",
          })],
        }));
      }
    } else if (filename.includes("dedication")) {
      // Optional italic centered
      const content = md.trim();
      if (!content.startsWith("[")) {
        fm.push(new Paragraph({
          spacing: { before: 0, after: 200 },
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: content,
            font: FONT, size: 22, color: BODY_COLOR, italics: true,
          })],
        }));
      }
    } else if (filename.includes("epigraph")) {
      // Italic centered quote + attribution
      const paras = md.split(/\n\s*\n/).map(p => p.trim()).filter(p => p && !p.startsWith("["));
      for (let i = 0; i < paras.length; i++) {
        const isQuote = i === 0;
        let text = paras[i].replace(/\n/g, " ").replace(/^\*+|\*+$/g, "");
        if (text.startsWith("—")) text = text.substring(1).trim();
        fm.push(new Paragraph({
          spacing: { before: 0, after: isQuote ? 320 : 80 },
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text,
            font: FONT,
            size: isQuote ? 20 : 16,
            color: isQuote ? BODY_COLOR : "666666",
            italics: isQuote,
          })],
        }));
      }
    } else {
      // Fallback: render as centered paragraphs
      const parsed = parseMarkdown(md, { centerParagraphs: true });
      fm.push(...parsed);
    }
  }
  return fm;
}

// ============================================================
// Contents (auto-TOC)
// ============================================================
function buildContents() {
  const c = [];
  c.push(new Paragraph({
    spacing: { before: 1800, after: 600 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: "CONTENTS", font: FONT, size: 24, color: BODY_COLOR, characterSpacing: 80, bold: true,
    })],
  }));
  c.push(new TableOfContents("Table of Contents", {
    hyperlink: false,
    headingStyleRange: "1-1",
    stylesWithLevels: [new StyleLevel("Heading1", 1)],
  }));
  return c;
}

// ============================================================
// Cycle body section
// ============================================================
function buildCycleSection(filename) {
  const cycleNum = cycleNumberFromFilename(filename);
  if (!cycleNum) throw new Error(`Cannot parse cycle number from ${filename}`);
  const cycleWord = CYCLE_WORDS[cycleNum];
  if (!cycleWord) throw new Error(`No word for cycle number ${cycleNum}`);

  const md = fs.readFileSync(path.join(SRC_DIR, filename), "utf8");
  const out = [];

  // Cycle H1 — script-generated, not in the file
  // (Cycle files start directly with prose; the H1 is added by the generator.)
  out.push(...createH1(`Cycle ${cycleWord}`, /* withPageBreak */ false));

  // Cycle 14 preserves blank lines for the half-page white space
  const isFinalCycle = cycleNum === 14;
  const parsed = parseMarkdown(md, {
    skipFirstH1PageBreak: true,
    preserveBlankLines: isFinalCycle,
  });
  out.push(...parsed);

  return out;
}

// ============================================================
// Back matter section
//
// Each filled-in back-matter file owns its own `# Title` H1. The generator
// does NOT add an additional H1 from the filename — that produces a
// double-H1 page (one blank, one with content).
//
// Convention: filled back-matter files start with `# Title` then content.
// Stub files start with `[` placeholder text and are skipped entirely.
//
// Special case: back_05_print_colophon.md gets small italic centered
// treatment (no H1, just a typography credit block at the very end).
// ============================================================
function buildBackMatterSection(filename) {
  const md = fs.readFileSync(path.join(SRC_DIR, filename), "utf8");
  const content = md.trim();

  // Skip stubs that haven't been filled in yet
  if (content.startsWith("[")) return null;

  // Print colophon: small italic centered, no H1
  if (filename === "back_05_print_colophon.md") {
    const out = [];
    out.push(new Paragraph({ spacing: { before: 2400 } }));
    const paras = md.split(/\n\s*\n/).map(p => p.trim()).filter(p => p && !p.startsWith("["));
    for (const para of paras) {
      out.push(new Paragraph({
        spacing: { before: 120, after: 120 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({
          text: para.replace(/\n/g, " "),
          font: FONT, size: 14, color: "666666", italics: true,
        })],
      }));
    }
    return out;
  }

  // Other back-matter: render the markdown directly. The file's own `# Title`
  // line provides the H1 (one per section). skipFirstH1PageBreak: false
  // because we want each back-matter section to start on its own page.
  return parseMarkdown(md, { skipFirstH1PageBreak: false });
}

// ============================================================
// Section page properties
// ============================================================
function bodyPageProps(opts = {}) {
  const props = {
    type: SectionType.ODD_PAGE,
    page: {
      size: { width: PAGE_W, height: PAGE_H, orientation: "portrait" },
      margin: {
        top: MARGIN_TOP,
        bottom: MARGIN_BOTTOM,
        left: MARGIN_GUTTER,
        right: MARGIN_OUTSIDE,
        header: 360,
        footer: 420,
        gutter: 0,
      },
      mirror: true,
    },
  };
  if (opts.startPage) {
    props.page.pageNumbers = { start: opts.startPage };
  }
  return props;
}

function bodyHeaders() {
  return {
    default: new Header({
      children: [new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 0 },
        children: [new TextRun({
          text: BOOK_TITLE,
          font: FONT, size: 14, color: "AAAAAA", characterSpacing: 40,
        })],
      })],
    }),
  };
}

function bodyFooters() {
  return {
    default: new Footer({
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({
          children: [PageNumber.CURRENT],
          font: FONT, size: 16, color: "999999",
        })],
      })],
    }),
  };
}

function frontMatterPageProps(opts = {}) {
  return {
    type: opts.type || SectionType.NEXT_PAGE,
    page: {
      size: { width: PAGE_W, height: PAGE_H, orientation: "portrait" },
      margin: {
        top: MARGIN_TOP,
        bottom: MARGIN_BOTTOM,
        left: MARGIN_GUTTER,
        right: MARGIN_OUTSIDE,
        header: 0,
        footer: 0,
        gutter: 0,
      },
      mirror: true,
    },
  };
}

// CRITICAL: explicit empty Header/Footer for any section that should be
// header/footer-free. Word inherits from previous section otherwise.
// See Inside_The_Region addendum 7 (KDP rejection on trailing blank page).
function emptyHeadersFooters() {
  return {
    headers: { default: new Header({ children: [new Paragraph({})] }) },
    footers: { default: new Footer({ children: [new Paragraph({})] }) },
  };
}

// ============================================================
// BUILD SECTIONS
// ============================================================
const sections = [];

// 1. Front matter — single section, no headers/footers
sections.push({
  properties: frontMatterPageProps(),
  ...emptyHeadersFooters(),
  children: buildFrontMatter(),
});

// 2. Contents — own ODD_PAGE section, no headers/footers
sections.push({
  properties: frontMatterPageProps({ type: SectionType.ODD_PAGE }),
  ...emptyHeadersFooters(),
  children: buildContents(),
});

// 3. Body — one section per cycle
const cycleFiles = discoverCycleFiles();
if (cycleFiles.length === 0) {
  console.warn("WARNING: no cycle_NN_*.md files found in", SRC_DIR);
}
let isFirstBody = true;
let totalBodyParagraphs = 0;
for (const filename of cycleFiles) {
  const children = buildCycleSection(filename);
  totalBodyParagraphs += children.length;
  sections.push({
    properties: bodyPageProps(isFirstBody ? { startPage: 1 } : {}),
    headers: bodyHeaders(),
    footers: bodyFooters(),
    children,
  });
  isFirstBody = false;
}

// 4. Back matter — one section per back_NN_*.md file
//    Each back matter section is ODD_PAGE (starts on recto) with
//    its own headers/footers (running header + page numbers continue).
const backMatterFiles = discoverFiles("back");
for (const filename of backMatterFiles) {
  const children = buildBackMatterSection(filename);
  if (children === null) continue;  // Stub not filled in
  sections.push({
    properties: bodyPageProps(),
    headers: bodyHeaders(),
    footers: bodyFooters(),
    children,
  });
}

// 5. Trailing EVEN_PAGE blank for even total page count.
// CRITICAL: empty headers/footers (Inside_The_Region addendum 7).
// DEFENSIVE: use truly empty `new Paragraph({})` (no TextRun) so the
// trailing page contains zero glyph content. KDP rejection for "text
// outside margins" on the last page has recurred across books even with
// the empty-headers-footers fix; the root cause is sometimes a tiny
// TextRun (even with white color or size:2) being detected as content.
// Empty Paragraph with no children is the safest construction.
sections.push({
  properties: {
    type: SectionType.EVEN_PAGE,
    page: {
      size: { width: PAGE_W, height: PAGE_H, orientation: "portrait" },
      margin: { top: MARGIN_TOP, bottom: MARGIN_BOTTOM, left: MARGIN_GUTTER, right: MARGIN_OUTSIDE, header: 0, footer: 0, gutter: 0 },
      mirror: true,
    },
  },
  ...emptyHeadersFooters(),
  children: [new Paragraph({})],
});

// ============================================================
// CREATE DOCUMENT
// ============================================================
const doc = new Document({
  features: { updateFields: true },
  styles: {
    default: {
      document: { run: { font: FONT, size: BODY_SIZE, color: BODY_COLOR } },
      heading1: {
        run: { font: FONT, size: 28, color: BODY_COLOR, bold: true },
        paragraph: { alignment: AlignmentType.CENTER },
      },
    },
  },
  sections,
});

// ============================================================
// WRITE + INJECT MIRROR MARGINS
// ============================================================
(async () => {
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
  const buffer = await Packer.toBuffer(doc);

  // docx@9 silently drops the per-section mirror flag. Inject manually
  // into word/settings.xml so Word actually mirror-margins the output.
  const zip = await JSZip.loadAsync(buffer);
  let settings = await zip.file("word/settings.xml").async("string");
  if (!settings.includes("mirrorMargins")) {
    settings = settings.replace("</w:settings>", "  <w:mirrorMargins/>\n</w:settings>");
    zip.file("word/settings.xml", settings);
  }
  const finalBuffer = await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  fs.writeFileSync(OUT_PATH, finalBuffer);

  console.log("\n=== KDP PRINT INTERIOR (paperback + hardcover) ===");
  console.log(`Written: ${OUT_PATH}`);
  console.log(`Size: ${(finalBuffer.length / 1024).toFixed(0)} KB`);
  console.log(`Sections: ${sections.length}`);
  console.log(`Cycle files: ${cycleFiles.length}`);
  console.log(`Back matter files (filled): ${sections.length - cycleFiles.length - 3}`);
  console.log(`Total paragraphs: ${totalBodyParagraphs}`);
  console.log(`Trim: 6" x 9"`);
  console.log(`Margins: top 0.5" / bottom 0.625" / gutter 0.875" / outside 0.5" (mirror enabled)`);
  console.log(`Recto enforcement: each body section is ODD_PAGE`);
  console.log(`Page numbers: footer center; restart at 1 on first body page`);
  console.log(`Running header: "${BOOK_TITLE}" centered, light gray`);
  console.log(`Trailing blank: EVEN_PAGE guarantees even total`);
  console.log("");
  console.log("Next: run update_print_interior.py to populate TOC, count pages, and emit PDF.");
})();
