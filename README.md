# NoteReady AI Starter

NoteReady AI is a source-grounded educational workspace. This starter implements the first two workflows:

1. Generate level-sensitive lecture notes from a detailed course outline.
2. Summarise uploaded notes, papers, slides and other text-based documents.

It also exports generated content to DOCX.

## Supported files in version 0.1

- PDF with extractable text
- DOCX
- PPTX
- TXT
- Markdown

Scanned PDFs and image-only documents need OCR, which is intentionally left for the next phase.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## AI configuration

Set both variables in `.env` or Render:

```text
OPENAI_API_KEY=your_server_side_key
OPENAI_MODEL=a_model_available_to_your_account
```

Without these variables, the app runs in development-preview mode. Upload, extraction, form handling and DOCX export remain testable, but no full AI output is generated.

The backend uses the OpenAI Responses API through `client.responses.create(...)`, which is the current general interface for text generation in the official OpenAI API documentation.

## Important safeguards already included

- No silent truncation. Long uploads return a visible extraction warning.
- No invented sources, statistics, authors or publication details in the generation instructions.
- Missing evidence is marked for lecturer input.
- Academic depth changes with the selected level.
- Course weeks, credit hours and contact hours are included in the lecture-note plan.
- Ghanaian and African examples are requested where relevant.
- The API key stays on the server.

## Recommended next build phases

### Phase 2: complete lecture-note production

- Parse the course outline into a confirmed topic map before generation.
- Generate one topic or teaching week at a time to protect completeness.
- Add project saving, regeneration and revision.
- Add editable rich-text preview.
- Add lecturer-only notes and student-facing notes as separate outputs.
- Add PowerPoint-ready lecture outlines.
- Add quizzes, assignments and marking schemes.
- Add references supplied by the lecturer as a separate source collection.

### Phase 3: long jobs and richer inputs

- PostgreSQL projects and users.
- Redis-backed job queue.
- Render background worker for long documents and audio.
- Object storage for uploads and exports.
- OCR for scanned notes and handwriting.
- Audio transcription with timestamps and speaker separation.
- Mind maps and flashcards.

### Phase 4: commercialisation

- Authentication and account dashboard.
- Usage entitlements by pages, audio minutes or course-note projects.
- Paystack and Stripe with NoteReady-specific product metadata and reference prefixes.
- Admin dashboard, audit logs and institutional plans.

## Suggested project boundaries

NoteReady AI should support lecturers and students in preparing editable learning materials. It should not present generated notes as a substitute for lecturer review or the original source. Important facts, citations, calculations and policy statements should be checked before use.
