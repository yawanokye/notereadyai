from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import Settings, get_settings
from app.schemas import (
    AcademicLevel,
    CourseModule,
    EssayQuestion,
    ExportRequest,
    GenerateResponse,
    LectureBatchResponse,
    LectureJobResponse,
    ObjectiveQuestion,
    SummaryMode,
)
from app.services.ai import AIService
from app.services.export_docx import build_docx
from app.services.extraction import extract_upload
from app.services.jobs import JobStore
from app.services.markdown_render import render_markdown
from app.services.outline import derive_modules
from app.services.prompts import assessment_prompt, lecture_batch_prompt, summary_prompt

router = APIRouter(prefix="/api", tags=["generation"])


@router.post("/lecture-notes/jobs", response_model=LectureJobResponse)
async def create_lecture_job(
    file: UploadFile = File(...),
    academic_level: AcademicLevel = Form(...),
    course_title: str = Form(""),
    course_code: str = Form(""),
    credit_hours: int = Form(3, ge=1, le=12),
    teaching_weeks: int = Form(13, ge=1, le=52),
    contact_hours_per_week: float = Form(3.0, gt=0, le=30),
    citation_style: str = Form("APA 7th edition"),
    context_preference: str = Form(
        "Use Ghanaian and African examples where relevant, alongside international examples."
    ),
    settings: Settings = Depends(get_settings),
) -> LectureJobResponse:
    try:
        extracted = await extract_upload(file, settings.max_extracted_chars)
        resolved_title = course_title.strip() or Path(file.filename or "Course Outline").stem
        modules = derive_modules(extracted.text, teaching_weeks)
        if not modules:
            raise ValueError("No teachable units could be identified in the uploaded outline.")

        store = JobStore(settings.generated_files_dir)
        job = store.create(
            {
                "title": f"{resolved_title} Lecture Notes",
                "course_title": resolved_title,
                "course_code": course_code.strip(),
                "source_filename": file.filename or "uploaded-file",
                "source_text": extracted.text,
                "extracted_characters": extracted.character_count,
                "extraction_warning": extracted.warning,
                "metadata": {
                    "academic_level": academic_level.value,
                    "credit_hours": credit_hours,
                    "teaching_weeks": teaching_weeks,
                    "contact_hours_per_week": contact_hours_per_week,
                    "citation_style": citation_style,
                    "context_preference": context_preference,
                },
                "modules": [
                    {
                        "id": module.id,
                        "sequence": module.sequence,
                        "title": module.title,
                        "source_text": module.source_text,
                    }
                    for module in modules
                ],
            }
        )
        return LectureJobResponse(
            job_id=job["job_id"],
            title=job["title"],
            source_filename=job["source_filename"],
            extracted_characters=job["extracted_characters"],
            extraction_warning=job.get("extraction_warning"),
            modules=[
                CourseModule(id=m["id"], sequence=m["sequence"], title=m["title"])
                for m in job["modules"]
            ],
            ai_enabled=settings.ai_enabled,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Course planning failed: {exc}") from exc


@router.post(
    "/lecture-notes/jobs/{job_id}/batches/{module_id}",
    response_model=LectureBatchResponse,
)
def generate_lecture_batch(
    job_id: str,
    module_id: str,
    settings: Settings = Depends(get_settings),
) -> LectureBatchResponse:
    store = JobStore(settings.generated_files_dir)
    try:
        job = store.load(job_id)
        cached = job.get("batches", {}).get(module_id)
        if cached:
            cached["cached"] = True
            return LectureBatchResponse.model_validate(cached)

        module = next((item for item in job["modules"] if item["id"] == module_id), None)
        if module is None:
            raise ValueError("The requested course unit was not found.")

        metadata = job["metadata"]
        academic_level = AcademicLevel(metadata["academic_level"])
        prompt = lecture_batch_prompt(
            course_title=job["course_title"],
            course_code=job.get("course_code", ""),
            module_title=module["title"],
            module_sequence=module["sequence"],
            total_modules=len(job["modules"]),
            module_source=module["source_text"],
            course_context=job["source_text"][:25_000],
            academic_level=academic_level,
            credit_hours=metadata["credit_hours"],
            teaching_weeks=metadata["teaching_weeks"],
            contact_hours_per_week=metadata["contact_hours_per_week"],
            citation_style=metadata["citation_style"],
            context_preference=metadata["context_preference"],
        )
        ai = AIService(settings)
        notes = ai.generate(
            prompt,
            max_tokens=settings.lecture_batch_max_tokens,
            temperature=0.18,
        )

        objective_questions: list[ObjectiveQuestion] = []
        essay_questions: list[EssayQuestion] = []
        assessment_warning = None
        try:
            assessment_data = ai.generate_json(
                assessment_prompt(
                    module_title=module["title"],
                    academic_level=academic_level,
                    notes=notes,
                ),
                max_tokens=settings.assessment_max_tokens,
                temperature=0.1,
            )
            objective_questions, essay_questions, assessment_warning = _normalise_assessment(
                assessment_data, module_id
            )
        except Exception as exc:  # Notes remain available even if assessment formatting fails.
            assessment_warning = f"Practice questions could not be prepared for this unit: {exc}"

        combined_markdown = notes.rstrip()
        if objective_questions or essay_questions:
            combined_markdown += "\n\n" + _assessment_markdown(
                objective_questions, essay_questions
            )

        payload = LectureBatchResponse(
            job_id=job_id,
            module_id=module_id,
            sequence=module["sequence"],
            total_modules=len(job["modules"]),
            title=module["title"],
            content_markdown=combined_markdown,
            content_html=render_markdown(combined_markdown),
            objective_questions=objective_questions,
            essay_questions=essay_questions,
            assessment_warning=assessment_warning,
            cached=False,
        )
        job.setdefault("batches", {})[module_id] = payload.model_dump()
        store.save(job)
        return payload
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lecture unit generation failed: {exc}") from exc


@router.post("/summaries/generate", response_model=GenerateResponse)
async def generate_summary(
    file: UploadFile = File(...),
    mode: SummaryMode = Form(SummaryMode.detailed),
    title: str = Form(""),
    settings: Settings = Depends(get_settings),
) -> GenerateResponse:
    try:
        extracted = await extract_upload(file, settings.max_extracted_chars)
        output = AIService(settings).generate(
            summary_prompt(source_text=extracted.text, mode=mode),
            max_tokens=settings.summary_max_tokens,
            temperature=0.15,
        )
        resolved_title = title.strip() or f"{Path(file.filename or 'Document').stem} Summary"
        return GenerateResponse(
            title=resolved_title,
            content_markdown=output,
            content_html=render_markdown(output),
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


def _normalise_assessment(
    data: dict[str, Any], module_id: str
) -> tuple[list[ObjectiveQuestion], list[EssayQuestion], str | None]:
    objective: list[ObjectiveQuestion] = []
    essays: list[EssayQuestion] = []

    for index, item in enumerate(data.get("objective_questions", [])[:10], start=1):
        if not isinstance(item, dict):
            continue
        options = [str(value).strip() for value in item.get("options", []) if str(value).strip()]
        if len(options) != 4 or not str(item.get("question", "")).strip():
            continue
        raw_correct = item.get("correct_index", 0)
        if isinstance(raw_correct, str) and raw_correct.upper() in {"A", "B", "C", "D"}:
            correct_index = ord(raw_correct.upper()) - ord("A")
        else:
            try:
                correct_index = int(raw_correct)
            except (TypeError, ValueError):
                correct_index = 0
        if correct_index not in range(4):
            correct_index = 0
        objective.append(
            ObjectiveQuestion(
                id=f"{module_id}-mcq-{index}",
                question=str(item["question"]).strip(),
                options=options,
                correct_index=correct_index,
                explanation=str(item.get("explanation", "Review the relevant section of the notes.")).strip(),
            )
        )

    for index, item in enumerate(data.get("essay_questions", [])[:3], start=1):
        if not isinstance(item, dict) or not str(item.get("question", "")).strip():
            continue
        points = [str(value).strip() for value in item.get("marking_points", []) if str(value).strip()]
        essays.append(
            EssayQuestion(
                id=f"{module_id}-essay-{index}",
                question=str(item["question"]).strip(),
                marking_points=points or ["A clear answer grounded in the lecture notes."],
            )
        )

    warnings: list[str] = []
    if len(objective) < 10:
        warnings.append(f"Only {len(objective)} of 10 valid objective questions were returned.")
    if len(essays) < 3:
        warnings.append(f"Only {len(essays)} of 3 valid essay questions were returned.")
    return objective, essays, " ".join(warnings) or None


def _assessment_markdown(
    objective_questions: list[ObjectiveQuestion],
    essay_questions: list[EssayQuestion],
) -> str:
    lines = ["## Review Questions"]
    if objective_questions:
        lines.extend(["", "### Objective Test"])
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for number, question in enumerate(objective_questions, start=1):
            lines.append(f"{number}. {question.question}")
            for index, option in enumerate(question.options):
                lines.append(f"   - {letters[index]}. {option}")
    if essay_questions:
        lines.extend(["", "### Essay Questions"])
        for number, question in enumerate(essay_questions, start=1):
            lines.append(f"{number}. {question.question}")
    return "\n".join(lines)
