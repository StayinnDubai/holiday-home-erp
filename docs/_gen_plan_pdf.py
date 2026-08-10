"""One-off script: renders the approved build plan (markdown) into a PDF.
Not part of the app; kept in docs/ for reference/re-generation only.
"""
import re
import sys
from pathlib import Path
from fpdf import FPDF

SRC = Path(r"C:\Users\Radik Hayriyan\.claude\plans\i-m-planning-to-create-steady-koala.md")
OUT = Path(__file__).parent / "holiday-home-erp-v1-build-plan.pdf"

ASCII_MAP = {
    "\u2014": "-", "\u2013": "-", "\u2192": "->", "\u00b7": "*",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u00a7": "Section ", "\u2026": "...", "\u2022": "-", "\u00d7": "x",
}


def clean(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    for uni, ascii_ in ASCII_MAP.items():
        text = text.replace(uni, ascii_)
    return text.encode("latin-1", "replace").decode("latin-1")


def safe_multicell(pdf: FPDF, h: float, text: str, chunk: int = 40):
    """multi_cell over the full remaining width, hard-wrapping any token wider than `chunk`."""
    words = text.split(" ")
    out_words = []
    for word in words:
        while len(word) > chunk:
            out_words.append(word[:chunk])
            word = word[chunk:]
        out_words.append(word)
    pdf.set_x(pdf.l_margin if pdf.get_x() < pdf.l_margin else pdf.get_x())
    pdf.multi_cell(0, h, " ".join(out_words))


class PlanPDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", size=8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def build():
    pdf = PlanPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(18, 16, 18)
    pdf.add_page()
    pdf.set_title("Holiday Home ERP - v1 Build Plan")
    pdf.set_left_margin(18)

    in_code = False
    raw_lines = SRC.read_text(encoding="utf-8").splitlines()

    for lineno, raw in enumerate(raw_lines, start=1):
        line = raw.rstrip()
        try:
            if line.strip().startswith("```"):
                in_code = not in_code
                continue

            if in_code:
                pdf.set_x(18)
                pdf.set_font("Courier", size=8)
                pdf.set_text_color(40, 40, 40)
                safe_multicell(pdf, 4, clean(line) if line else " ")
                continue

            if not line.strip():
                pdf.ln(2)
                continue

            if line.strip() == "---":
                pdf.ln(1)
                pdf.set_draw_color(200, 200, 200)
                y = pdf.get_y()
                pdf.line(18, y, 192, y)
                pdf.ln(4)
                continue

            if line.strip().startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if all(re.fullmatch(r"-+", c.replace(":", "")) for c in cells):
                    continue
                pdf.set_x(18)
                pdf.set_font("Helvetica", size=8.5)
                pdf.set_text_color(20, 20, 20)
                row_text = "  |  ".join(clean(c) for c in cells)
                safe_multicell(pdf, 4.6, row_text)
                continue

            m = re.match(r"^(#{1,4})\s+(.*)$", line)
            if m:
                level = len(m.group(1))
                text = clean(m.group(2))
                sizes = {1: 17, 2: 13.5, 3: 11.5, 4: 10.5}
                pdf.ln(3 if level <= 2 else 2)
                pdf.set_x(18)
                pdf.set_font("Helvetica", style="B", size=sizes.get(level, 10))
                pdf.set_text_color(10, 10, 10)
                safe_multicell(pdf, 7 if level <= 2 else 6, text)
                pdf.ln(1)
                continue

            if line.strip().startswith(("- ", "* ")):
                text = clean(line.strip()[2:])
                pdf.set_x(18)
                pdf.set_font("Helvetica", size=9.5)
                pdf.set_text_color(20, 20, 20)
                safe_multicell(pdf, 5, f"-  {text}")
                continue

            m2 = re.match(r"^(\d+)\.\s+(.*)$", line.strip())
            if m2:
                text = clean(m2.group(2))
                pdf.set_x(18)
                pdf.set_font("Helvetica", size=9.5)
                pdf.set_text_color(20, 20, 20)
                safe_multicell(pdf, 5, f"{m2.group(1)}. {text}")
                continue

            pdf.set_x(18)
            pdf.set_font("Helvetica", size=9.5)
            pdf.set_text_color(20, 20, 20)
            safe_multicell(pdf, 5, clean(line))

        except Exception:
            print(f"FAILED at line {lineno}: x={pdf.get_x():.1f} w={pdf.w:.1f} rm={pdf.r_margin:.1f} lm={pdf.l_margin:.1f}", file=sys.stderr)
            print(f"  content: {line!r}", file=sys.stderr)
            raise

    pdf.output(str(OUT))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
