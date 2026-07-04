from enum import Enum

from pydantic import BaseModel, Field


class AcademicLevel(str, Enum):
    senior_high = "Senior high school"
    certificate_diploma = "Certificate or diploma"
    undergraduate_100 = "Undergraduate Level 100"
    undergraduate_200 = "Undergraduate Level 200"
    undergraduate_300 = "Undergraduate Level 300"
    undergraduate_400 = "Undergraduate Level 400"
    postgraduate_diploma = "Postgraduate diploma"
    non_research_masters = "Non-research master's"
    research_masters = "Research master's or MPhil"
    professional_doctorate = "Professional doctorate"
    phd = "PhD"


class SummaryMode(str, Enum):
    concise = "Concise summary"
    detailed = "Detailed summary"
    academic = "Academic paper summary"
    executive = "Executive summary"
    meeting = "Meeting minutes and action items"
    revision = "Revision notes"


class CourseModule(BaseModel):
    id: str
    sequence: int
    title: str


class LectureJobResponse(BaseModel):
    job_id: str
    title: str
    source_filename: str
    extracted_characters: int
    extraction_warning: str | None = None
    modules: list[CourseModule]
    ai_enabled: bool


class ObjectiveQuestion(BaseModel):
    id: str
    question: str
    options: list[str] = Field(min_length=2, max_length=6)
    correct_index: int = Field(ge=0)
    explanation: str


class EssayQuestion(BaseModel):
    id: str
    question: str
    marking_points: list[str]


class LectureBatchResponse(BaseModel):
    job_id: str
    module_id: str
    sequence: int
    total_modules: int
    title: str
    content_markdown: str
    content_html: str
    objective_questions: list[ObjectiveQuestion]
    essay_questions: list[EssayQuestion]
    assessment_warning: str | None = None
    cached: bool = False


class GenerateResponse(BaseModel):
    title: str
    content_markdown: str
    content_html: str
    source_filename: str
    extracted_characters: int
    extraction_warning: str | None = None
    ai_enabled: bool


class ExportRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content_markdown: str = Field(min_length=1)
