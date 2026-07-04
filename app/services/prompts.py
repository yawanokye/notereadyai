from app.schemas import AcademicLevel, SummaryMode


LEVEL_GUIDANCE: dict[AcademicLevel, str] = {
    AcademicLevel.senior_high: (
        "Use accessible language, short conceptual steps, familiar examples, guided practice "
        "and frequent checks for understanding."
    ),
    AcademicLevel.certificate_diploma: (
        "Use practical explanations, procedures, workplace applications and limited abstraction."
    ),
    AcademicLevel.undergraduate_100: (
        "Introduce concepts carefully, define every technical term, use guided examples and "
        "build from description to basic application."
    ),
    AcademicLevel.undergraduate_200: (
        "Develop conceptual understanding, comparisons and moderate analytical application."
    ),
    AcademicLevel.undergraduate_300: (
        "Provide deeper theory, applied analysis, comparison of perspectives and case-based learning."
    ),
    AcademicLevel.undergraduate_400: (
        "Use advanced analysis, current evidence, critical evaluation and integrative applications."
    ),
    AcademicLevel.postgraduate_diploma: (
        "Combine advanced professional application with critical conceptual discussion."
    ),
    AcademicLevel.non_research_masters: (
        "Emphasise advanced professional judgement, current evidence and complex applications."
    ),
    AcademicLevel.research_masters: (
        "Provide critical theoretical analysis, methodological awareness and research-led discussion."
    ),
    AcademicLevel.professional_doctorate: (
        "Integrate frontier evidence, professional problem-solving, critical synthesis and practice contribution."
    ),
    AcademicLevel.phd: (
        "Use doctoral depth, theoretical contestation, frontier literature, methodological critique "
        "and original lines of inquiry."
    ),
}


def lecture_batch_prompt(
    *,
    course_title: str,
    course_code: str,
    module_title: str,
    module_sequence: int,
    total_modules: int,
    module_source: str,
    course_context: str,
    academic_level: AcademicLevel,
    credit_hours: int,
    teaching_weeks: int,
    contact_hours_per_week: float,
    citation_style: str,
    context_preference: str,
) -> str:
    target_words = round(max(1_600, min(4_200, contact_hours_per_week * 900)))
    return f"""
Prepare one publication-quality, web-ready lecture unit. This is batch {module_sequence} of {total_modules}; do not attempt to write the whole course.

COURSE
Title: {course_title}
Code: {course_code or '[not supplied]'}
Academic level: {academic_level.value}
Credit hours: {credit_hours}
Teaching weeks: {teaching_weeks}
Approximate contact hours for this unit: {contact_hours_per_week}
Unit title: {module_title}
Context preference: {context_preference}
Citation style: {citation_style}
Target length: approximately {target_words:,} words, adjusted to the genuine complexity of the topic.

LEVEL AND PEDAGOGY
{LEVEL_GUIDANCE[academic_level]}
Write as an experienced lecturer in the discipline. The notes must teach, not merely list definitions.

REQUIRED STRUCTURE
# {module_title}

## Learning outcomes
Provide 4-7 measurable outcomes, progressing across appropriate Bloom levels.

## Topic overview
Explain why the topic matters and connect it to the course.

## Main lecture content
Use logically numbered subheadings. For every major concept:
- define it precisely;
- explain how and why it works;
- distinguish it from related concepts;
- provide a relevant example or application;
- discuss limitations, assumptions or common errors where applicable.

Include worked calculations step by step when the source contains a quantitative method. Do not skip intermediate reasoning.

## Applied illustration or mini-case
Use a credible Ghanaian or African context when appropriate, but do not invent exact company facts, policy claims, statistics or events. Generic realistic examples are acceptable when clearly presented as illustrations.

## In-class learning activity
Provide a practical activity with instructions, expected output and approximate duration.

## Common misconceptions and lecturer emphasis
Identify points students often misunderstand and state what the lecturer should emphasise.

## Key takeaways
Provide 5-8 concise synthesis points.

## Further reading
List only readings explicitly named in the supplied outline or sources you can state accurately with high confidence. When no dependable source is available, write [LECTURER TO ADD A VERIFIED READING].

QUALITY RULES
1. Stay within the supplied course outline and the source extract for this unit.
2. Do not repeat course metadata, disclaimers or statements about being AI-generated.
3. Do not expose planning instructions, source warnings or verification notes in the student-facing lecture notes.
4. Use polished Markdown. Use genuine Markdown tables where comparison, classification or worked data improves learning.
5. Keep tables readable: no more than four columns, short cell text, clear column headings and no paragraph-length cells.
6. Do not use raw HTML, fake tables made with spaces, or decorative separators made from repeated dashes.
7. Avoid unsupported citations. Never invent a reference, DOI, quotation, law, date, policy or statistic.
8. Avoid shallow bullet-only writing. Use developed paragraphs, examples and transitions.
9. Do not use future tense to describe established concepts or completed procedures.
10. Do not number questions continuously from previous units.

COURSE OUTLINE CONTEXT
---
{course_context}
---

SOURCE EXTRACT FOR THIS UNIT
---
{module_source}
---
""".strip()


def assessment_prompt(*, module_title: str, academic_level: AcademicLevel, notes: str) -> str:
    return f"""
Create a practice assessment for the lecture unit titled "{module_title}" at {academic_level.value}.
Use only the lecture notes below.

Return exactly this JSON structure:
{{
  "objective_questions": [
    {{
      "question": "A clear single-best-answer question",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0,
      "explanation": "Why the answer is correct and why the main distractor is wrong"
    }}
  ],
  "essay_questions": [
    {{
      "question": "An analytical or applied essay question",
      "marking_points": ["Expected point 1", "Expected point 2", "Expected point 3"]
    }}
  ]
}}

ASSESSMENT REQUIREMENTS
- Produce exactly 10 objective questions, each with exactly four plausible options.
- correct_index must be an integer from 0 to 3.
- Distribute correct answers across A, B, C and D rather than repeating one position.
- Include recall, understanding, application and analysis at a level appropriate to {academic_level.value}.
- Avoid trick wording, double negatives, "all of the above" and ambiguous alternatives.
- Produce exactly 3 essay questions, including at least one applied case or problem.
- Give 4-6 concise marking points for each essay question.
- Do not add facts not contained in the notes.

LECTURE NOTES
---
{notes}
---
""".strip()


def summary_prompt(*, source_text: str, mode: SummaryMode) -> str:
    mode_instructions = {
        SummaryMode.concise: "Produce a compact summary of the central ideas and essential details.",
        SummaryMode.detailed: (
            "Produce a thorough, readable and well-organised summary that preserves qualifications, "
            "evidence and relationships among ideas."
        ),
        SummaryMode.academic: (
            "Identify purpose, concepts, theories, methods, evidence, findings, limitations and implications where present."
        ),
        SummaryMode.executive: (
            "Present the issue, major findings, implications, decisions and recommended actions for a professional audience."
        ),
        SummaryMode.meeting: (
            "Produce meeting minutes with discussion themes, decisions, action items, owners and deadlines. "
            "Do not invent missing owners or dates."
        ),
        SummaryMode.revision: (
            "Create organised revision notes with definitions, concepts, examples, memory prompts, "
            "10 objective review questions and 3 essay questions."
        ),
    }
    return f"""
You are a careful source-grounded academic summarisation specialist.

TASK
{mode_instructions[mode]}

RULES
1. Use only the supplied source.
2. Do not add facts, names, figures, conclusions or references absent from the source.
3. Preserve important limitations, conditions, uncertainty and competing views.
4. Flag genuinely unclear source content as [SOURCE UNCLEAR], but do not clutter the output with process commentary.
5. Use polished Markdown headings, developed paragraphs and concise genuine tables where useful.
6. Tables must have no more than four columns and must remain readable on a phone or laptop screen.
7. Do not leave Markdown symbols as visible prose or use raw HTML.
8. End with "Points to verify against the original" only when the source itself is unclear or inconsistent.

SOURCE
---
{source_text}
---
""".strip()
