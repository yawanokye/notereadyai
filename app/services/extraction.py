from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import fitz
from docx import Document
from fastapi import UploadFile
from pptx import Presentation


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md"}


@dataclass(slots=True)
class ExtractionResult:
    text: str
    character_count: int
    warning: str | None = None


def _clean_text(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    cleaned: list[str] = []
    blank_seen = False
    for line in lines:
        if line.strip():
            cleaned.append(line)
            blank_seen = False
        elif not blank_seen:
            cleaned.append("")
            blank_seen = True
    return "\n".join(cleaned).strip()


def _extract_pdf(data: bytes) -> str:
    document = fitz.open(stream=data, filetype="pdf")
    pages = [page.get_text("text") for page in document]
    return "\n\n".join(pages)


def _extract_docx(data: bytes) -> str:
    document = Document(BytesIO(data))
    parts: list[str] = []
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            parts.append(paragraph.text)
    for table in document.tables:
        for row in table.rows:
            values = [cell.text.strip() for cell in row.cells]
            if any(values):
                parts.append(" | ".join(values))
    return "\n".join(parts)


def _extract_pptx(data: bytes) -> str:
    presentation = Presentation(BytesIO(data))
    slides: list[str] = []
    for index, slide in enumerate(presentation.slides, start=1):
        items: list[str] = [f"Slide {index}"]
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                items.append(shape.text.strip())
        slides.append("\n".join(items))
    return "\n\n".join(slides)


async def extract_upload(upload: UploadFile, max_chars: int) -> ExtractionResult:
    filename = upload.filename or "uploaded-file"
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported file type. Upload one of: {supported}.")

    data = await upload.read()
    if not data:
        raise ValueError("The uploaded file is empty.")

    if extension == ".pdf":
        text = _extract_pdf(data)
    elif extension == ".docx":
        text = _extract_docx(data)
    elif extension == ".pptx":
        text = _extract_pptx(data)
    else:
        text = data.decode("utf-8", errors="replace")

    text = _clean_text(text)
    if not text:
        raise ValueError(
            "No readable text was extracted. The file may contain scanned pages. "
            "OCR support belongs in the next development phase."
        )

    original_count = len(text)
    warning = None
    if original_count > max_chars:
        text = text[:max_chars]
        warning = (
            f"The file contained {original_count:,} characters. Only the first "
            f"{max_chars:,} characters were processed. Increase MAX_EXTRACTED_CHARS "
            "or add chunked processing before production use."
        )

    return ExtractionResult(text=text, character_count=len(text), warning=warning)
