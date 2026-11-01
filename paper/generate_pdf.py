"""
generate_pdf.py
---------------
Converts the MAGI+ paper Markdown to PDF.
Uses fpdf2's HTML renderer for robust output.

Usage:
    python paper/generate_pdf.py
"""

import os
import re
import unicodedata
import markdown
from fpdf import FPDF, HTMLMixin

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_MD   = os.path.join(SCRIPT_DIR, "our_paper", "MAGI_Plus_Draft_v1.md")
OUTPUT_PDF = os.path.join(SCRIPT_DIR, "our_paper", "MAGI_Plus_Draft_v1.pdf")
OUTPUT_HTML = os.path.join(SCRIPT_DIR, "our_paper", "MAGI_Plus_Draft_v1.html")


# ─────────────────────────────────────────────
# TEXT CLEANING
# ─────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Normalize text for PDF-safe output."""
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '--', '\u2026': '...',
        '\u2192': '->', '\u2190': '<-', '\u2265': '>=', '\u2264': '<=',
        '\u03ba': 'kappa', '\u03b1': 'alpha', '\u03b2': 'beta',
        '\u00b0': 'deg', '\u00b1': '+/-',
        '\u2714': '[YES]', '\u274c': '[NO]', '\u26a0': '[WARN]',
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    # Normalize remaining accented chars
    normalized = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in normalized
                   if unicodedata.category(c) != 'Mn' and ord(c) < 256)
    # Remove remaining non-ASCII
    text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
    return text


# ─────────────────────────────────────────────
# MARKDOWN → CLEAN HTML
# ─────────────────────────────────────────────

def md_to_clean_html(md_text: str) -> str:
    """Convert Markdown to clean HTML suitable for fpdf2 HTMLMixin."""
    # Clean the text first
    md_text = clean_text(md_text)

    # Convert markdown tables to HTML using python-markdown
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])
    html = md.convert(md_text)
    return html


# ─────────────────────────────────────────────
# PDF CLASS
# ─────────────────────────────────────────────

class PDF(FPDF, HTMLMixin):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(140, 140, 140)
            self.cell(
                0, 5,
                "MAGI+: From Diagnosis to Action in Automated Psychiatric Interviews",
                align="L"
            )
            self.ln(4)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 5, f"- {self.page_no()} -", align="C")


# ─────────────────────────────────────────────
# SECTION-BY-SECTION APPROACH
# ─────────────────────────────────────────────

def build_pdf_section_by_section(md_text: str) -> PDF:
    """
    Build PDF by processing each line/section of the markdown,
    avoiding overflow issues with manual rendering.
    """
    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(25, 22, 25)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_title("MAGI+: From Diagnosis to Action in Automated Psychiatric Interviews")
    pdf.set_author("MAGI+ Research Team")

    lines = clean_text(md_text).split('\n')
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin

    in_code = False
    code_buf = []
    in_table = False
    table_header_done = False

    def flush_code():
        nonlocal code_buf
        if not code_buf:
            return
        pdf.set_font("Courier", size=7)
        pdf.set_fill_color(245, 245, 245)
        for cl in code_buf[:50]:
            safe = cl[:120]
            pdf.set_x(pdf.l_margin + 3)
            pdf.cell(usable_w - 6, 4.5, safe, fill=True, ln=True)
        pdf.ln(2)
        code_buf = []

    for raw_line in lines:
        line = raw_line.rstrip()

        # ── Code blocks ──────────────────
        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue

        # ── Tables ───────────────────────
        if '|' in line and line.strip().startswith('|'):
            stripped = line.strip()
            # Skip separator rows
            if re.match(r'^\|[\s\-:|]+\|', stripped):
                continue
            cols = [c.strip()[:40] for c in stripped.strip('|').split('|')]
            n = len(cols)
            if n == 0:
                continue
            col_w = usable_w / n

            if not in_table:
                in_table = True
                table_header_done = False

            if not table_header_done:
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.set_fill_color(50, 50, 90)
                pdf.set_text_color(255, 255, 255)
                for col in cols:
                    pdf.cell(col_w, 5.5, col, border=1, fill=True)
                pdf.ln()
                table_header_done = True
            else:
                pdf.set_font("Times", "", 7.5)
                pdf.set_fill_color(250, 250, 250)
                pdf.set_text_color(0, 0, 0)
                for col in cols:
                    pdf.cell(col_w, 5.5, col, border=1)
                pdf.ln()
            pdf.set_text_color(0, 0, 0)
            continue
        else:
            if in_table:
                in_table = False
                table_header_done = False
                pdf.ln(2)

        # ── Headings ─────────────────────
        if line.startswith('# ') and not line.startswith('## '):
            pdf.set_font("Helvetica", "B", 15)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(usable_w, 8, line[2:].strip(), align="C")
            pdf.ln(3)
            continue

        if line.startswith('## '):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_fill_color(235, 235, 245)
            pdf.set_text_color(0, 0, 80)
            pdf.cell(usable_w, 7, line[3:].strip(), fill=True, ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)
            continue

        if line.startswith('### '):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(usable_w, 6, line[4:].strip())
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)
            continue

        if line.startswith('#### '):
            pdf.set_font("Helvetica", "BI", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(usable_w, 6, line[5:].strip())
            pdf.set_text_color(0, 0, 0)
            continue

        # ── Horizontal rule ──────────────
        if line.strip() in ('---', '***', '___'):
            pdf.ln(2)
            pdf.set_draw_color(180, 180, 180)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)
            continue

        # ── Blockquote ───────────────────
        if line.startswith('> '):
            pdf.set_font("Times", "I", 9.5)
            pdf.set_text_color(80, 80, 80)
            pdf.set_x(pdf.l_margin + 6)
            pdf.multi_cell(usable_w - 6, 5.5, line[2:].strip())
            pdf.set_text_color(0, 0, 0)
            continue

        # ── Bullet list ──────────────────
        if re.match(r'^(\s*)[-*] ', line):
            indent_chars = len(line) - len(line.lstrip())
            level = indent_chars // 2
            text = re.sub(r'^(\s*)[-*] ', '', line)
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            text = re.sub(r'`(.*?)`', r'\1', text)
            pdf.set_font("Times", "", 10)
            pdf.set_x(pdf.l_margin + 4 + level * 5)
            pdf.cell(5, 5.5, chr(149))  # bullet char
            pdf.set_x(pdf.l_margin + 9 + level * 5)
            pdf.multi_cell(usable_w - 9 - level * 5, 5.5, text.strip())
            continue

        # ── Numbered list ────────────────
        m = re.match(r'^(\d+)\. (.*)', line)
        if m:
            num = m.group(1)
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', m.group(2))
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            pdf.set_font("Times", "", 10)
            pdf.set_x(pdf.l_margin + 4)
            pdf.cell(7, 5.5, f"{num}.")
            pdf.set_x(pdf.l_margin + 11)
            pdf.multi_cell(usable_w - 11, 5.5, text.strip())
            continue

        # ── Empty line ───────────────────
        if not line.strip():
            pdf.ln(2)
            continue

        # ── Skip draft note ──────────────
        if line.startswith('**Draft') or line.startswith('*Draft'):
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(150, 150, 150)
            clean = re.sub(r'\*+', '', line).strip()
            pdf.cell(usable_w, 5, clean, align="C", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(3)
            continue

        # ── Keywords line ────────────────
        if line.startswith('**Keywords'):
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(60, 60, 60)
            clean = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
            clean = re.sub(r'\*(.*?)\*', r'\1', clean)
            pdf.multi_cell(usable_w, 5.5, clean.strip())
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)
            continue

        # ── Regular paragraph ────────────
        clean = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', line)
        clean = re.sub(r'\*\*(.*?)\*\*', r'\1', clean)
        clean = re.sub(r'\*(.*?)\*', r'\1', clean)
        clean = re.sub(r'`(.*?)`', r'\1', clean)
        clean = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', clean)
        if clean.strip():
            pdf.set_font("Times", "", 10.5)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(usable_w, 5.8, clean.strip(), align="J")
            pdf.ln(1)

    return pdf


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print(f"Reading: {INPUT_MD}")
    with open(INPUT_MD, "r", encoding="utf-8") as f:
        md_text = f.read()

    print("Building PDF...")
    pdf = build_pdf_section_by_section(md_text)

    print(f"Saving: {OUTPUT_PDF}")
    pdf.output(OUTPUT_PDF)
    size_kb = round(os.path.getsize(OUTPUT_PDF) / 1024, 1)
    print(f"\n✅ PDF generated!")
    print(f"   File : {OUTPUT_PDF}")
    print(f"   Size : {size_kb} KB")
    print(f"   Pages: {pdf.page_no()}")


if __name__ == "__main__":
    main()
