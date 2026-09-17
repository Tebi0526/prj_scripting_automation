#!/usr/bin/env python3
"""Erzeugt aus einer Markdown-Datei ein PDF (reportlab).

Unterstützt genau die Auszeichnungen, die in unseren Dokumenten vorkommen:
Überschriften, Absätze, Aufzählungen, Tabellen, Bilder und Codeblöcke.

    python tools/md_zu_pdf.py docs/Technische_Dokumentation.md
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DARK = colors.HexColor("#1F4E78")
LIGHT = colors.HexColor("#D9EAF7")
GREY = colors.HexColor("#B7C9D6")

styles = getSampleStyleSheet()
STYLE = {
    "h1": ParagraphStyle("h1", parent=styles["Heading1"], fontSize=19, leading=23, textColor=DARK, spaceAfter=10),
    "h2": ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13.5, leading=17, textColor=DARK,
                         spaceBefore=16, spaceAfter=6),
    "h3": ParagraphStyle("h3", parent=styles["Heading3"], fontSize=11, leading=14, textColor=colors.HexColor("#2F4A5C"),
                         spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY,
                           spaceAfter=6),
    "cell": ParagraphStyle("cell", parent=styles["BodyText"], fontSize=8.5, leading=11, spaceAfter=0),
    "cellhead": ParagraphStyle("cellhead", parent=styles["BodyText"], fontSize=8.5, leading=11, spaceAfter=0,
                               textColor=colors.white, fontName="Helvetica-Bold"),
    "code": ParagraphStyle("code", parent=styles["BodyText"], fontName="Courier", fontSize=8, leading=10.5,
                           backColor=colors.HexColor("#F2F4F6"), borderPadding=6, spaceBefore=4, spaceAfter=8),
    "caption": ParagraphStyle("caption", parent=styles["BodyText"], fontSize=8, leading=10,
                              textColor=colors.HexColor("#5A6B77"), spaceBefore=2, spaceAfter=10),
}

MAX_IMAGE_WIDTH = 16.0 * cm
MAX_IMAGE_HEIGHT = 23.0 * cm


def inline(text: str) -> str:
    """Wandelt **fett**, *kursiv* und `code` in reportlab-Markup um."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r'<font face="Courier" size="8.5">\1</font>', text)
    return text


def build_table(rows: list[list[str]]) -> Table:
    """Baut eine Tabelle mit Kopfzeile; Spaltenbreiten nach Textlänge verteilt."""
    header, body = rows[0], rows[2:]  # Zeile 1 ist die Trennlinie
    columns = list(range(len(header)))
    total_width = 16.0 * cm

    def longest_word(index: int) -> int:
        words = [word for cell in [header[index]] + [row[index] for row in body] for word in cell.split()]
        return max((len(word) for word in words), default=4)

    def longest_cell(index: int) -> int:
        return max(len(header[index]), *(len(row[index]) for row in body)) if body else len(header[index])

    # Mindestbreite verhindert, dass einzelne Woerter umbrochen werden.
    minimums = [min(6.0 * cm, longest_word(index) * 0.17 * cm + 0.5 * cm) for index in columns]
    weights = [longest_cell(index) for index in columns]
    weight_sum = sum(weights) or 1
    widths = [max(minimums[index], total_width * weights[index] / weight_sum) for index in columns]

    overflow = sum(widths) - total_width
    if overflow > 0:
        slack = [widths[index] - minimums[index] for index in columns]
        slack_sum = sum(slack) or 1
        widths = [widths[index] - overflow * slack[index] / slack_sum for index in columns]

    data = [[Paragraph(inline(cell), STYLE["cellhead"]) for cell in header]]
    data += [[Paragraph(inline(cell), STYLE["cell"]) for cell in row] for row in body]

    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def scaled_image(path: Path) -> Image:
    """Skaliert ein Bild proportional auf die Seitenbreite.

    Sehr breite Grafiken (Klassendiagramm) werden um 90 Grad gedreht und
    seitenfuellend gesetzt, sonst waeren die Beschriftungen unleserlich.
    """
    path = _rotate_if_wide(path)
    image = Image(str(path))
    ratio = image.imageHeight / image.imageWidth
    width = min(MAX_IMAGE_WIDTH, image.imageWidth)
    height = width * ratio
    if height > MAX_IMAGE_HEIGHT:
        height = MAX_IMAGE_HEIGHT
        width = height / ratio
    image.drawWidth, image.drawHeight = width, height
    image.hAlign = "CENTER"
    return image


def _rotate_if_wide(path: Path) -> Path:
    """Dreht Grafiken mit einem Seitenverhaeltnis ueber 1.3 hochkant."""
    from PIL import Image as PilImage

    with PilImage.open(path) as picture:
        if picture.width / picture.height <= 1.3:
            return path
        rotated_path = Path(tempfile.gettempdir()) / f"{path.stem}_gedreht{path.suffix}"
        picture.rotate(90, expand=True).save(rotated_path)
    return rotated_path


def convert(md_path: Path, pdf_path: Path) -> Path:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    story: list = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        # Codeblock
        if stripped.startswith("```"):
            index += 1
            block = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
                index += 1
            index += 1
            story.append(Paragraph("<br/>".join(line or "&nbsp;" for line in block), STYLE["code"]))
            continue

        # Tabelle
        if stripped.startswith("|"):
            block = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                block.append(cells)
                index += 1
            story.append(build_table(block))
            story.append(Spacer(1, 8))
            continue

        # Bild
        image_match = re.match(r"!\[(.*?)\]\((.+?)\)", stripped)
        if image_match:
            target = (md_path.parent / image_match.group(2)).resolve()
            if target.exists():
                from PIL import Image as PilImage

                with PilImage.open(target) as picture:
                    is_wide = picture.width / picture.height > 1.3
                if is_wide:
                    story.append(PageBreak())
                else:
                    story.append(Spacer(1, 4))
                story.append(scaled_image(target))
                story.append(Paragraph(inline(image_match.group(1)), STYLE["caption"]))
            index += 1
            continue

        # Überschriften
        heading = re.match(r"(#{1,3})\s+(.*)", stripped)
        if heading:
            level = len(heading.group(1))
            if level == 2 and any(isinstance(item, (Table, Image)) for item in story[-3:]):
                story.append(Spacer(1, 6))
            story.append(Paragraph(inline(heading.group(2)), STYLE[f"h{level}"]))
            index += 1
            continue

        # Aufzählung
        if stripped.startswith("- "):
            items = []
            while index < len(lines) and lines[index].strip().startswith("- "):
                items.append(ListItem(Paragraph(inline(lines[index].strip()[2:]), STYLE["body"]), leftIndent=12))
                index += 1
            story.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=14))
            continue

        # Absatz (zusammenhängende Zeilen zusammenfassen)
        block = []
        while index < len(lines) and lines[index].strip() and not re.match(r"^(#|\||```|- |!\[)", lines[index].strip()):
            block.append(lines[index].strip())
            index += 1
        story.append(Paragraph(inline(" ".join(block).replace("  ", "<br/>")), STYLE["body"]))

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#5A6B77"))
        canvas.drawString(2.2 * cm, 1.3 * cm, md_path.stem.replace("_", " "))
        canvas.drawRightString(A4[0] - 2.2 * cm, 1.3 * cm, f"Seite {document.page}")
        canvas.setStrokeColor(GREY)
        canvas.line(2.2 * cm, 1.6 * cm, A4[0] - 2.2 * cm, 1.6 * cm)
        canvas.restoreState()

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.2 * cm,
        title=md_path.stem.replace("_", " "),
        author="David Stalder, Thibaud Ueckert",
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return pdf_path


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    for argument in sys.argv[1:]:
        source = Path(argument)
        target = source.with_suffix(".pdf")
        convert(source, target)
        print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
