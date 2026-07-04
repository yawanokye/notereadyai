from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import Settings, get_settings
from app.schemas import AcademicLevel, ExportRequest, GenerateResponse, SummaryMode
from app.services.ai import AIService
from app.services.export_docx import build_docx
from app.services.extraction import extract_upload
from app.services.prompts import lecture_notes_prompt, summary_prompt

router = APIRouter(prefix="/api", tags=["generation"])


@router.post("/lecture-notes/generate", response_model=GenerateResponse)
async def generate_lecture_notes(
    file: UploadFile = File(...),
    academic_level: AcademicLevel = Form(...),
    course_title: str = Form(""),
    course_code: str = Form(""),
    credit_hours: int = Form(3, ge=1, le=12),
    teaching_weeks: int = Form(13, ge=1, le=52),
    contact_hours_per_week: float = Form(3.0, gt=0, le=30),
    citation_style: str = Form("APA 7th edition"),
    context_preference: str = Form("Use Ghanaian and African examples where relevant, alongside international examples."),
    settings: Settings = Depends(get_settings),
) -> GenerateResponse:
    try:
        extracted = await extract_upload(file, settings.max_extracted_chars)
        prompt = lecture_notes_prompt(
            source_text=extracted.text,
            academic_level=academic_level,
            course_title=course_title,
            course_code=course_code,
            credit_hours=credit_hours,
            teaching_weeks=teaching_weeks,
            contact_hours_per_week=contact_hours_per_week,
            citation_style=citation_style,
            context_preference=context_preference,
        )
        output = AIService(settings).generate(prompt)
        resolved_title = course_title.strip() or Path(file.filename or "Course Outline").stem
        return GenerateResponse(
            title=f"{resolved_title} Lecture Notes",
            content_markdown=output,
            source_filename=file.filename or "uploaded-file",
            extracted_characters=extracted.character_count,
            extraction_warning=extracted.warning,
            ai_enabled=settings.ai_enabled,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lecture-note generation failed: {exc}") from exc


@router.post("/summaries/generate", response_model=GenerateResponse)
async def generate_summary(
    file: UploadFile = File(...),
    mode: SummaryMode = Form(SummaryMode.detailed),
    title: str = Form(""),
    settings: Settings = Depends(get_settings),
) -> GenerateResponse:
    try:
        extracted = await extract_upload(file, settings.max_extracted_chars)
        output = AIService(settings).generate(summary_prompt(source_text=extracted.text, mode=mode))
        resolved_title = title.strip() or f"{Path(file.filename or 'Document').stem} Summary"
        return GenerateResponse(
            title=resolved_title,
            content_markdown=output,
            source_filename=file.filename or "uploaded-file",
            extracted_characters=extracted.character_count,
            extraction_warning=extracted.warning,
            ai_enabled=settings.ai_enabled,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {exc}") from exc


@router.post("/exports/docx")
def export_docx(
    payload: ExportRequest,
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    path = build_docx(payload.title, payload.content_markdown, settings.generated_files_dir)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{path.stem}.docx",
    )
