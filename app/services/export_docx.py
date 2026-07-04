import re
import uuid
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET = re.compile(r"^[-*]\s+(.*)$")
_NUMBERED = re.compile(r"^\d+[.)]\s+(.*)$")


def _add_markdown_line(document: Document, line: str) -> None:
    heading = _HEADING.match(line)
    if heading:
        level = min(len(heading.group(1)), 4)
        document.add_heading(heading.group(2).strip(), level=level)
        return

    bullet = _BULLET.match(line)
    if bullet:
        document.add_paragraph(bullet.group(1).strip(), style="List Bullet")
        return

    numbered = _NUMBERED.match(line)
    if numbered:
        document.add_paragraph(numbered.group(1).strip(), style="List Number")
        return

    if line.strip():
        document.add_paragraph(line.strip())
    else:
        document.add_paragraph()


def build_docx(title: str, markdown_text: str, output_dir: Path) -> Path:
    document = Document()
    styles = document.styles
    styles["Normal"].font.name = "Aptos"
    styles["Normal"].font.size = Pt(11)

    title_paragraph = document.add_paragraph()
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_paragraph.add_run(title)
    run.bold = True
    run.font.size = Pt(18)

    for line in markdown_text.splitlines():
        _add_markdown_line(document, line)

    filename = f"{uuid.uuid4().hex}_{_safe_filename(title)}.docx"
    path = output_dir / filename
    document.save(path)
    return path


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    return cleaned[:80] or "noteready_output"
