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


class GenerateResponse(BaseModel):
    title: str
    content_markdown: str
    source_filename: str
    extracted_characters: int
    extraction_warning: str | None = None
    ai_enabled: bool


class ExportRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content_markdown: str = Field(min_length=1)
