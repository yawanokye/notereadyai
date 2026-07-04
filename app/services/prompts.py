from app.schemas import AcademicLevel, SummaryMode


LEVEL_GUIDANCE: dict[AcademicLevel, str] = {
    AcademicLevel.senior_high: "Use accessible language, guided explanations, familiar examples and frequent checks for understanding.",
    AcademicLevel.certificate_diploma: "Use practical explanations, procedural examples and workplace applications.",
    AcademicLevel.undergraduate_100: "Introduce core concepts carefully, define terms and use guided examples.",
    AcademicLevel.undergraduate_200: "Develop conceptual understanding and include moderate analytical application.",
    AcademicLevel.undergraduate_300: "Provide deeper theory, applied analysis, comparison of perspectives and case-based learning.",
    AcademicLevel.undergraduate_400: "Use advanced analysis, research evidence, critical evaluation and integrative applications.",
    AcademicLevel.postgraduate_diploma: "Combine advanced professional application with critical conceptual discussion.",
    AcademicLevel.non_research_masters: "Emphasise advanced professional judgement, current evidence and complex applications.",
    AcademicLevel.research_masters: "Provide critical theoretical analysis, methodological awareness and research-led discussion.",
    AcademicLevel.professional_doctorate: "Integrate frontier evidence, professional problem-solving, critical synthesis and practice contribution.",
    AcademicLevel.phd: "Use doctoral depth, theoretical contestation, frontier literature, methodological critique and original lines of inquiry.",
}


def lecture_notes_prompt(
    *,
    source_text: str,
    academic_level: AcademicLevel,
    course_title: str,
    course_code: str,
    credit_hours: int,
    teaching_weeks: int,
    contact_hours_per_week: float,
    citation_style: str,
    context_preference: str,
) -> str:
    level_instruction = LEVEL_GUIDANCE[academic_level]
    return f"""
You are an expert university curriculum developer and lecturer. Prepare complete, editable lecture notes from the detailed course outline supplied below.

COURSE INFORMATION
Course title: {course_title or '[derive from the source where possible]'}
Course code: {course_code or '[derive from the source where possible]'}
Academic level: {academic_level.value}
Credit hours: {credit_hours}
Teaching weeks: {teaching_weeks}
Contact hours per week: {contact_hours_per_week}
Citation style: {citation_style}
Context preference: {context_preference}

DEPTH REQUIREMENT
{level_instruction}

NON-NEGOTIABLE RULES
1. Follow the uploaded course outline closely. Cover every identifiable topic and subtopic without adding unrelated material.
2. First provide a course coverage map that distributes the outline across {teaching_weeks} teaching weeks and respects approximately {contact_hours_per_week} contact hours per week.
3. Then prepare detailed lecture notes for each week or major topic.
4. Each topic should contain: learning outcomes aligned with Bloom's taxonomy, introduction, key concepts, detailed explanations, relevant theories or models, examples, applications, tables or text-described diagrams where useful, a local or regional illustration where relevant, class activity, discussion questions, key-point summary, self-assessment questions and recommended readings.
5. Match the complexity, language, examples and assessments to {academic_level.value}.
6. Use only sources that are genuinely known and verifiable. Never invent references, statistics, quotations, authors, DOIs or publication details.
7. When adequate source evidence is not available, write [LECTURER TO ADD A VERIFIED SOURCE] rather than fabricating a citation.
8. Clearly separate information derived from the uploaded outline from expanded teaching content.
9. Use Markdown headings and tables. Do not include raw HTML.
10. End with a consolidated reference list in {citation_style} style, containing only works cited in the notes.
11. Mark any missing course information as [LECTURER INPUT REQUIRED].

DETAILED COURSE OUTLINE
---
{source_text}
---
""".strip()


def summary_prompt(*, source_text: str, mode: SummaryMode) -> str:
    mode_instructions = {
        SummaryMode.concise: "Produce a compact summary of the central ideas and essential details.",
        SummaryMode.detailed: "Produce a thorough structured summary that preserves qualifications, evidence and relationships among ideas.",
        SummaryMode.academic: "Identify the purpose, concepts, theories, methods, evidence, findings, limitations and implications where present.",
        SummaryMode.executive: "Present the issue, major findings, implications, decisions and recommended actions for a professional audience.",
        SummaryMode.meeting: "Produce meeting minutes with discussion themes, decisions, action items, owners and deadlines. Do not invent missing owners or dates.",
        SummaryMode.revision: "Create organised revision notes with definitions, concepts, examples, memory prompts and self-test questions.",
    }
    return f"""
You are a careful source-grounded summarisation assistant.

TASK
{mode_instructions[mode]}

RULES
1. Use only the supplied source.
2. Do not add facts, names, figures, conclusions or references that do not appear in the source.
3. Preserve important limitations, conditions and uncertainty.
4. Flag unclear passages as [SOURCE UNCLEAR].
5. Use Markdown headings and concise tables where helpful.
6. End with a section called "Verification points" listing names, figures, dates or claims that a user should check against the original.

SOURCE
---
{source_text}
---
""".strip()
