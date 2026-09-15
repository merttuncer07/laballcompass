from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "LABALLCOMPASS_R193_R208_AKADEMIK_RAPOR.md"
OUT = HERE.parents[1] / "output" / "pdf" / "LABALLCOMPASS_R193_R208_AKADEMIK_RAPOR.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "C:/Windows/Fonts/arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", "C:/Windows/Fonts/ariali.ttf"))
pdfmetrics.registerFont(TTFont("CambriaMath", "C:/Windows/Fonts/cambria.ttc", subfontIndex=0))

NAVY = colors.HexColor("#203748")
BLUE = colors.HexColor("#2E74B5")
DARK_BLUE = colors.HexColor("#1F4D78")
MUTED = colors.HexColor("#667085")
LIGHT = colors.HexColor("#F4F6F9")
TABLE_HEAD = colors.HexColor("#E8EEF5")
TABLE_ALT = colors.HexColor("#F8FAFC")
GRID = colors.HexColor("#CBD5E1")
INK = colors.HexColor("#111827")


class ReportDocTemplate(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=LETTER,
            leftMargin=inch,
            rightMargin=inch,
            topMargin=0.84 * inch,
            bottomMargin=0.75 * inch,
            title="LabAllCompass R193-R208 Aktif Teori Portföyü",
            author="LabAllCompass",
            subject="Tarihî darboğazları yeniden ziyaret programı",
        )
        first_frame = Frame(inch, 0.75 * inch, 6.5 * inch, 9.5 * inch, id="first")
        body_frame = Frame(inch, 0.75 * inch, 6.5 * inch, 9.38 * inch, id="body")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[first_frame], onPage=self.cover_page),
            PageTemplate(id="body", frames=[body_frame], onPage=self.body_page),
        ])

    @staticmethod
    def cover_page(canvas, doc):
        canvas.saveState()
        canvas.setTitle("LabAllCompass R193-R208 Aktif Teori Portföyü")
        canvas.restoreState()

    @staticmethod
    def body_page(canvas, doc):
        canvas.saveState()
        width, height = LETTER
        canvas.setStrokeColor(colors.HexColor("#D8DEE7"))
        canvas.setLineWidth(0.35)
        canvas.line(inch, height - 0.55 * inch, width - inch, height - 0.55 * inch)
        canvas.setFont("Arial-Bold", 7.6)
        canvas.setFillColor(MUTED)
        canvas.drawString(inch, height - 0.44 * inch, "LABALLCOMPASS  |  AKTİF TEORİ PORTFÖYÜ R193-R208")
        canvas.setFont("Arial", 8)
        canvas.drawRightString(width - inch, 0.44 * inch, f"Sayfa {doc.page}")
        canvas.restoreState()


def make_styles():
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=9.65,
        leading=13.35,
        textColor=INK,
        alignment=TA_JUSTIFY,
        spaceAfter=7,
        allowWidows=0,
        allowOrphans=0,
    )
    h1 = ParagraphStyle(
        "H1", parent=body, fontName="Arial-Bold", fontSize=15.2, leading=18,
        textColor=BLUE, spaceBefore=15, spaceAfter=8, keepWithNext=True,
    )
    h2 = ParagraphStyle(
        "H2", parent=body, fontName="Arial-Bold", fontSize=12.4, leading=15,
        textColor=BLUE, spaceBefore=11, spaceAfter=5.5, keepWithNext=True,
    )
    h3 = ParagraphStyle(
        "H3", parent=body, fontName="Arial-Bold", fontSize=10.8, leading=13.2,
        textColor=DARK_BLUE, spaceBefore=8, spaceAfter=4, keepWithNext=True,
    )
    bullet = ParagraphStyle(
        "Bullet", parent=body, leftIndent=18, firstLineIndent=-10, bulletIndent=4,
        spaceAfter=4.5, leading=12.7,
    )
    numbered = ParagraphStyle(
        "Numbered", parent=body, leftIndent=22, firstLineIndent=-14,
        spaceAfter=4.5, leading=12.7,
    )
    equation = ParagraphStyle(
        "Equation", parent=body, fontName="CambriaMath", fontSize=9.25,
        leading=13.2, alignment=TA_CENTER, textColor=NAVY,
        backColor=LIGHT, borderPadding=(6, 8, 6, 8),
        leftIndent=9, rightIndent=9, spaceBefore=2, spaceAfter=7,
        splitLongWords=False,
    )
    table_cell = ParagraphStyle(
        "TableCell", parent=body, fontSize=7.7, leading=10, alignment=TA_LEFT,
        spaceAfter=0,
    )
    table_head = ParagraphStyle(
        "TableHead", parent=table_cell, fontName="Arial-Bold", textColor=NAVY,
    )
    reference = ParagraphStyle(
        "Reference", parent=body, fontSize=8.7, leading=11.6, leftIndent=14,
        firstLineIndent=-14, spaceAfter=4,
    )
    return {
        "body": body, "h1": h1, "h2": h2, "h3": h3,
        "bullet": bullet, "numbered": numbered, "equation": equation,
        "table": table_cell, "table_head": table_head, "reference": reference,
    }


ST = make_styles()


def inline_markup(text: str) -> str:
    # Arial's Windows face omits several mathematical Unicode glyphs. Equations
    # use Cambria Math; prose receives readable ASCII equivalents rather than
    # missing-glyph boxes.
    prose_map = {
        "ᐟ": "/", "⁺": "+", "⁻": "-",
        "₀": "_0", "₁": "_1", "₂": "_2", "₊": "+", "₋": "-", "₌": "=",
        "ₕ": "_h", "ₖ": "_k", "ₘ": "_m", "ₙ": "_n", "ₚ": "_p", "ₛ": "_s", "ₜ": "_t",
        "ℬ": "B", "ℳ": "M", "𝒜": "A", "𝒮": "S",
        "⇒": "=>", "⇔": "<=>", "∃": "exists ", "∇": "grad ", "∈": " in ",
        "∪": " union ", "≪": "<<", "⊆": " subset ", "⊕": " direct-sum ",
        "⊗": " tensor ", "⟨": "<", "⟩": ">", "⪰": " PSD>= ",
    }
    text = "".join(prose_map.get(ch, ch) for ch in text)
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`(.*?)`", r'<font name="CambriaMath" color="#1F4D78">\1</font>', escaped)
    escaped = re.sub(
        r"(https?://[^\s<]+)",
        lambda m: f'<link href="{m.group(1)}" color="#2E74B5">{m.group(1)}</link>',
        escaped,
    )
    return escaped


def add_cover(story):
    story.extend([
        Spacer(1, 0.85 * inch),
        Paragraph("LABALLCOMPASS", ParagraphStyle(
            "Kicker", fontName="Arial-Bold", fontSize=10.5, leading=13,
            alignment=TA_CENTER, textColor=BLUE, spaceAfter=14,
        )),
        Paragraph("Tarihî Darboğazları<br/>Yeniden Ziyaret Programı", ParagraphStyle(
            "CoverTitle", fontName="Arial-Bold", fontSize=28, leading=32,
            alignment=TA_CENTER, textColor=NAVY, spaceAfter=14,
        )),
        Paragraph("R193-R208 Aktif Teori Portföyü", ParagraphStyle(
            "CoverSubtitle", fontName="Arial", fontSize=15.5, leading=19,
            alignment=TA_CENTER, textColor=DARK_BLUE, spaceAfter=30,
        )),
        Paragraph("Matematiksel mekanizmalar, kırılan darboğazlar,<br/>negatif sonuçlar ve araştırma sınırları", ParagraphStyle(
            "CoverDeck", fontName="Arial-Italic", fontSize=11.4, leading=16,
            alignment=TA_CENTER, textColor=MUTED, spaceAfter=47,
        )),
        Paragraph("TEKNİK ARAŞTIRMA RAPORU", ParagraphStyle(
            "CoverLabel", fontName="Arial-Bold", fontSize=9.5, leading=12,
            alignment=TA_CENTER, textColor=BLUE, spaceAfter=14,
        )),
    ])
    metadata = [
        ["Sürüm", "R208 freeze"],
        ["Kapsam", "Aktif Lab tarihi R193-R208"],
        ["Tarih", "31 Ağustos 2026"],
        ["Durum", "Bağımsız incelemeye hazır çalışma kaydı"],
    ]
    data = [[Paragraph(f"<b>{html.escape(a)}</b>", ST["table"]), Paragraph(html.escape(b), ST["table"])] for a, b in metadata]
    table = Table(data, colWidths=[0.9 * inch, 3.7 * inch], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.4, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 24))
    story.append(Paragraph("Hakemli yayın veya küresel yenilik iddiası değildir.", ParagraphStyle(
        "CoverNote", fontName="Arial-Italic", fontSize=8.5, leading=11,
        alignment=TA_CENTER, textColor=MUTED,
    )))
    story.append(PageBreak())


def table_widths(rows):
    cols = len(rows[0])
    if cols == 2:
        first_len = max(len(r[0]) for r in rows)
        return [1.25 * inch, 5.25 * inch] if first_len <= 18 else [1.8 * inch, 4.7 * inch]
    if cols == 3:
        return [1.55 * inch, 3.3 * inch, 1.65 * inch]
    return [6.5 * inch / cols] * cols


def add_markdown_table(story, rows):
    data = []
    for r_idx, row in enumerate(rows):
        style = ST["table_head"] if r_idx == 0 else ST["table"]
        data.append([Paragraph(inline_markup(value), style) for value in row])
    table = Table(data, colWidths=table_widths(rows), repeatRows=1, hAlign="LEFT", splitByRow=1)
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEAD),
        ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
        ("BOX", (0, 0), (-1, -1), 0.45, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for idx in range(2, len(rows), 2):
        commands.append(("BACKGROUND", (0, idx), (-1, idx), TABLE_ALT))
    table.setStyle(TableStyle(commands))
    story.extend([table, Spacer(1, 6)])


def parse_story():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "# Öz")
    story = []
    add_cover(story)
    eq_idx = 0
    numbered_idx = 0
    i = start
    in_references = False
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == "---PAGEBREAK---":
            story.append(PageBreak())
            i += 1
            continue
        if line == ":::eq":
            eq_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                eq_lines.append(lines[i].strip())
                i += 1
            eq_idx += 1
            eq = " ".join(eq_lines)
            story.append(Paragraph(f"{html.escape(eq)}&nbsp;&nbsp;&nbsp;<font name=\"Arial\" size=\"7.4\" color=\"#667085\">[{eq_idx}]</font>", ST["equation"]))
            i += 1
            continue
        if line.startswith("|"):
            raw_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                raw_rows.append(lines[i].strip())
                i += 1
            rows = []
            for idx, raw in enumerate(raw_rows):
                cells = [c.strip() for c in raw.strip("|").split("|")]
                if idx == 1 and all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    continue
                rows.append(cells)
            add_markdown_table(story, rows)
            continue
        if line.startswith("# "):
            title = line[2:]
            if title.startswith("Ek "):
                story.append(PageBreak())
            in_references = title.startswith("Ek B") or title.startswith("Ek C")
            story.append(Paragraph(inline_markup(title), ST["h1"]))
            i += 1
            continue
        if line.startswith("## "):
            story.append(Paragraph(inline_markup(line[3:]), ST["h2"]))
            i += 1
            continue
        if line.startswith("### "):
            story.append(Paragraph(inline_markup(line[4:]), ST["h3"]))
            i += 1
            continue
        if re.match(r"^\d+\.\s+", line):
            marker, content = line.split(".", 1)
            story.append(Paragraph(f"<b>{marker}.</b>&nbsp;&nbsp;{inline_markup(content.strip())}", ST["numbered"]))
            i += 1
            continue
        if line.startswith("- "):
            story.append(Paragraph(inline_markup(line[2:]), ST["bullet"], bulletText="•"))
            i += 1
            continue

        paragraph_lines = [line]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                i += 1
                break
            if (nxt.startswith("#") or nxt.startswith("|") or nxt.startswith("- ")
                    or re.match(r"^\d+\.\s+", nxt) or nxt in (":::eq", "---PAGEBREAK---")):
                break
            paragraph_lines.append(nxt)
            i += 1
        style = ST["reference"] if in_references else ST["body"]
        story.append(Paragraph(inline_markup(" ".join(paragraph_lines)), style))
    return story


def main():
    doc = ReportDocTemplate(str(OUT))
    story = parse_story()
    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    main()
