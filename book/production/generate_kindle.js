const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, PageBreak,
  HeadingLevel, TableOfContents, StyleLevel,
} = require("docx");

// ============================================================
// KINDLE EBOOK GENERATOR — The Long Watch
// Reflowable .docx for direct KDP upload.
//
// No page numbers, no headers, no fixed margins, no mirror margins,
// no recto enforcement (all print concepts that look broken on Kindle).
//
// Heading 1 → Kindle navigable TOC entry
//   (Cycle One through Cycle Fourteen, plus back matter sections).
//
// Inline parsing: bold (**...**) and italic (*...*) only.
// No math, no code, no tables, no lists, no blockquotes
// (none used in The Long Watch).
//
// Section breaks: · · · (three middle dots) preserved as centered marks.
//
// Front matter: rendered programmatically from front_NN_*.md files.
//   Half-title and title page are NOT Heading 1 (redundant in
//   reflowable Kindle — they would clutter the TOC).
//
// Back matter: each back_NN_*.md becomes a Heading 1 navigable entry,
//   skipping any stub file that starts with "[" (unfilled).
// ============================================================

const FONT = "Georgia";
const TITLE_FONT = "Georgia";
const BODY_COLOR = "1A1A1A";
const BODY_SIZE = 24;       // 12pt — Kindle suggestion only; readers override
const BODY_LINE = 340;      // ~1.4x

// Book metadata
const BOOK_TITLE = "ASTRA-7: The Long Watch";
const AUTHOR_NAME = "Bo Chen";

// Cycle number-to-word for H1 chapter titles
const CYCLE_WORDS = [
  null, "One", "Two", "Three", "Four", "Five", "Six", "Seven",
  "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen",
];

// Back-matter files to skip in Kindle (print-only)
const KINDLE_SKIP_BACK = new Set(["back_05_print_colophon.md"]);

const SRC_DIR = "C:\\ASTRA-7\\book\\manuscript";
const OUT_PATH = "C:\\ASTRA-7\\book\\production\\outputs\\kindle\\The_Long_Watch_KINDLE.docx";

// ============================================================
// Inline run builder — bold + italic only
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

function createBodyParagraph(text) {
  const runs = buildInlineRuns(text, { font: FONT, size: BODY_SIZE, color: BODY_COLOR });
  return new Paragraph({
    spacing: { after: 160, line: BODY_LINE, lineRule: "atLeast" },
    indent: { firstLine: 360 },
    alignment: AlignmentType.JUSTIFIED,
    children: runs,
  });
}

function createH1(title) {
  return [
    new Paragraph({ children: [new PageBreak()] }),
    new Paragraph({ spacing: { before: 800, after: 200 } }),
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      spacing: { before: 200, after: 320 },
      alignment: AlignmentType.CENTER,
      children: [new TextRun({
        text: title, font: FONT, size: 32, color: BODY_COLOR, characterSpacing: 40, bold: true,
      })],
    }),
    new Paragraph({
      spacing: { before: 80, after: 480 },
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "\u2726", font: "Segoe UI Symbol", size: 22, color: "999999" })],
    }),
  ];
}

function createSectionBreak() {
  return new Paragraph({
    spacing: { before: 240, after: 240 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "\u00B7  \u00B7  \u00B7", font: "Segoe UI Symbol", size: 18, color: "999999" })],
  });
}

function createBlankLineParagraph() {
  return new Paragraph({
    spacing: { after: 0, line: 280, lineRule: "atLeast" },
    children: [new TextRun({ text: "", font: FONT, size: BODY_SIZE })],
  });
}

// ============================================================
// Markdown parser (simplified for The Long Watch)
// Handles only: H1, body paragraphs, · · · section breaks,
// optionally preserved blank lines.
// ============================================================
function parseMarkdown(text, opts = {}) {
  const lines = text.split("\n");
  const out = [];
  const preserveBlankLines = opts.preserveBlankLines === true;

  let i = 0;
  while (i < lines.length) {
    const stripped = lines[i].trim();

    if (stripped === "") {
      if (preserveBlankLines) out.push(createBlankLineParagraph());
      i++;
      continue;
    }

    const h1Match = stripped.match(/^#\s+(.+)$/);
    if (h1Match && !stripped.startsWith("##")) {
      out.push(...createH1(h1Match[1].trim()));
      i++;
      continue;
    }

    if (stripped === "\u00B7 \u00B7 \u00B7" || stripped === "\u00B7  \u00B7  \u00B7") {
      out.push(createSectionBreak());
      i++;
      continue;
    }

    // Body paragraph
    let paraLines = [stripped];
    i++;
    while (i < lines.length && lines[i].trim().length > 0) {
      const next = lines[i].trim();
      if (/^#{1,6}\s/.test(next)) break;
      if (next === "\u00B7 \u00B7 \u00B7" || next === "\u00B7  \u00B7  \u00B7") break;
      paraLines.push(next);
      i++;
    }
    out.push(createBodyParagraph(paraLines.join(" ")));
  }
  return out;
}

// ============================================================
// File discovery
// ============================================================
function discoverFiles(prefix) {
  if (!fs.existsSync(SRC_DIR)) return [];
  return fs.readdirSync(SRC_DIR)
    .filter(f => f.startsWith(`${prefix}_`) && f.endsWith(".md"))
    .sort();
}

function discoverCycleFiles() {
  return fs.readdirSync(SRC_DIR)
    .filter(f => /^cycle_\d{2}_.+\.md$/.test(f))
    .sort();
}

function cycleNumberFromFilename(filename) {
  const m = filename.match(/^cycle_(\d{2})_/);
  return m ? parseInt(m[1], 10) : null;
}

// ============================================================
// Front matter — Kindle convention
// Title page + copyright + dedication + epigraph rendered into
// the document. NOT marked as Heading 1 (would clutter the TOC).
// ============================================================
function buildFrontMatter() {
  const fm = [];

  // Title page
  fm.push(new Paragraph({ spacing: { before: 2400, after: 200 } }));
  fm.push(new Paragraph({
    spacing: { before: 200, after: 200 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: BOOK_TITLE, font: TITLE_FONT, size: 44, color: BODY_COLOR, bold: true, characterSpacing: 60,
    })],
  }));
  fm.push(new Paragraph({
    spacing: { before: 200, after: 200 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "\u2726", font: "Segoe UI Symbol", size: 22, color: "999999" })],
  }));
  fm.push(new Paragraph({
    spacing: { before: 200, after: 800 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: AUTHOR_NAME, font: TITLE_FONT, size: 24, color: BODY_COLOR, characterSpacing: 80,
    })],
  }));

  // Copyright
  fm.push(new Paragraph({ children: [new PageBreak()] }));
  const copyrightPath = path.join(SRC_DIR, "front_03_copyright.md");
  if (fs.existsSync(copyrightPath)) {
    const md = fs.readFileSync(copyrightPath, "utf8");
    const paras = md.split(/\n\s*\n/).map(p => p.trim()).filter(p => p && !p.startsWith("["));
    fm.push(new Paragraph({ spacing: { before: 800 } }));
    for (const para of paras) {
      fm.push(new Paragraph({
        spacing: { before: 80, after: 80 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({
          text: para.replace(/\n/g, " "),
          font: FONT, size: 18, color: "555555",
        })],
      }));
    }
  }

  // Dedication (skip if stub)
  const dedicationPath = path.join(SRC_DIR, "front_04_dedication.md");
  if (fs.existsSync(dedicationPath)) {
    const md = fs.readFileSync(dedicationPath, "utf8").trim();
    if (md && !md.startsWith("[")) {
      fm.push(new Paragraph({ children: [new PageBreak()] }));
      fm.push(new Paragraph({ spacing: { before: 1600 } }));
      fm.push(new Paragraph({
        spacing: { before: 1200, after: 200 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({
          text: md, font: FONT, size: 24, color: BODY_COLOR, italics: true,
        })],
      }));
    }
  }

  // Epigraph
  const epigraphPath = path.join(SRC_DIR, "front_05_epigraph.md");
  if (fs.existsSync(epigraphPath)) {
    const md = fs.readFileSync(epigraphPath, "utf8");
    const paras = md.split(/\n\s*\n/).map(p => p.trim()).filter(p => p && !p.startsWith("["));
    if (paras.length > 0) {
      fm.push(new Paragraph({ children: [new PageBreak()] }));
      fm.push(new Paragraph({ spacing: { before: 1600 } }));
      for (let i = 0; i < paras.length; i++) {
        const isQuote = i === 0;
        let text = paras[i].replace(/\n/g, " ").replace(/^\*+|\*+$/g, "");
        if (text.startsWith("—")) text = text.substring(1).trim();
        fm.push(new Paragraph({
          spacing: { before: isQuote ? 400 : 240, after: isQuote ? 320 : 80 },
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text,
            font: FONT,
            size: isQuote ? 22 : 18,
            color: isQuote ? BODY_COLOR : "666666",
            italics: isQuote,
          })],
        }));
      }
    }
  }

  return fm;
}

// ============================================================
// Auto-TOC (Kindle hyperlinked navigation)
// ============================================================
function buildContents() {
  const c = [];
  c.push(new Paragraph({ children: [new PageBreak()] }));
  c.push(new Paragraph({
    spacing: { before: 800, after: 600 },
    alignment: AlignmentType.CENTER,
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({
      text: "Contents", font: FONT, size: 28, color: BODY_COLOR, characterSpacing: 80, bold: true,
    })],
  }));
  c.push(new TableOfContents("Table of Contents", {
    hyperlink: true,   // Kindle wants hyperlinked TOC
    headingStyleRange: "1-1",
    stylesWithLevels: [new StyleLevel("Heading1", 1)],
  }));
  return c;
}

// ============================================================
// Cycle body section
// ============================================================
function buildCycleContent(filename) {
  const cycleNum = cycleNumberFromFilename(filename);
  if (!cycleNum) throw new Error(`Cannot parse cycle number from ${filename}`);
  const cycleWord = CYCLE_WORDS[cycleNum];
  if (!cycleWord) throw new Error(`No word for cycle number ${cycleNum}`);

  const md = fs.readFileSync(path.join(SRC_DIR, filename), "utf8");
  const out = [];

  // Cycle H1 (script-generated)
  out.push(...createH1(`Cycle ${cycleWord}`));

  // Cycle 14 preserves blank lines for white-space close
  const isFinalCycle = cycleNum === 14;
  out.push(...parseMarkdown(md, { preserveBlankLines: isFinalCycle }));

  return out;
}

// ============================================================
// Back matter section
//
// Each filled-in back-matter file owns its own `# Title` H1 (used by
// parseMarkdown to emit a navigable Kindle H1). The generator does NOT
// add an additional H1 from filename — that would double-H1 the section.
// ============================================================
function buildBackMatterContent(filename) {
  if (KINDLE_SKIP_BACK.has(filename)) return null;  // Print-only files

  const md = fs.readFileSync(path.join(SRC_DIR, filename), "utf8").trim();
  if (md.startsWith("[")) return null;  // Stub not filled in

  return parseMarkdown(md);
}

// ============================================================
// BUILD CHILDREN
// ============================================================
const children = [];

// 1. Front matter (no Heading 1, not navigable)
children.push(...buildFrontMatter());

// 2. Contents (Heading 1, navigable)
children.push(...buildContents());

// 3. Body cycles (Heading 1 per cycle, navigable)
const cycleFiles = discoverCycleFiles();
if (cycleFiles.length === 0) {
  console.warn("WARNING: no cycle_NN_*.md files found in", SRC_DIR);
}
let totalParagraphs = 0;
for (const filename of cycleFiles) {
  const parsed = buildCycleContent(filename);
  totalParagraphs += parsed.length;
  children.push(...parsed);
}

// 4. Back matter (Heading 1 per filled-in section, navigable)
const backMatterFiles = discoverFiles("back");
let backMatterEmitted = 0;
for (const filename of backMatterFiles) {
  const content = buildBackMatterContent(filename);
  if (content === null) continue;
  children.push(...content);
  backMatterEmitted++;
}

// ============================================================
// CREATE DOCUMENT (single section, reflowable)
// ============================================================
const doc = new Document({
  features: { updateFields: true },
  styles: {
    default: {
      document: { run: { font: FONT, size: BODY_SIZE, color: BODY_COLOR } },
      heading1: {
        run: { font: FONT, size: 32, color: BODY_COLOR, bold: true },
        paragraph: { alignment: AlignmentType.CENTER },
      },
    },
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840, orientation: "portrait" } } },
    children,
  }],
});

// ============================================================
// WRITE
// ============================================================
(async () => {
  const outDir = path.dirname(OUT_PATH);
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(OUT_PATH, buffer);

  console.log("\n=== KINDLE EBOOK ===");
  console.log(`Written: ${OUT_PATH}`);
  console.log(`Size: ${(buffer.length / 1024).toFixed(0)} KB`);
  console.log(`Cycle files: ${cycleFiles.length}`);
  console.log(`Back matter sections (filled): ${backMatterEmitted}`);
  console.log(`Total paragraphs: ${totalParagraphs}`);
  console.log("");
  console.log("Next: run update_kindle_toc.py to populate the TOC field.");
})();
