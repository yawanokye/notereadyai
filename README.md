# NoteReady AI 0.2

NoteReady AI converts course outlines and source documents into web-readable lecture notes, interactive practice questions and polished DOCX files.

## Main improvements in version 0.2

- Generates lecture notes one course unit at a time instead of one oversized request.
- Shows completed units immediately while later units continue generating.
- Provides a full-screen reading workspace with unit navigation and adjustable text size.
- Renders Markdown as real web headings, lists and responsive tables.
- Generates 10 objective questions and 3 essay questions for each lecture unit.
- Provides an interactive objective-test practice area with scores, correct answers and explanations.
- Provides revealable essay marking guides.
- Exports real Word headings, bold text, lists, tables, page numbers, a cover and a contents page.
- Preserves the order of paragraphs and tables when extracting DOCX files.
- Preserves slide titles and tables when extracting PPTX files.

## Project structure

```text
app/
  main.py
  config.py
  schemas.py
  routers/generation.py
  services/
    ai.py
    export_docx.py
    extraction.py
    jobs.py
    markdown_render.py
    outline.py
    prompts.py
  static/
    index.html
    styles.css
    app.js
tests/
requirements.txt
render.yaml
.python-version
```

## Local setup

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then add the DeepSeek key.

```env
DEEPSEEK_API_KEY=your_actual_key
DEEPSEEK_MODEL=deepseek-v4-pro
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

Run:

```bash
uvicorn app.main:app --reload
```

## Render deployment

When the repository contains `app`, `requirements.txt` and `render.yaml` at its top level, leave **Root Directory blank**.

Build command:

```bash
python -m pip install --upgrade pip setuptools wheel && python -m pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Required environment variables:

```env
PYTHON_VERSION=3.12.11
ENVIRONMENT=production
DEEPSEEK_API_KEY=your_actual_key
DEEPSEEK_MODEL=deepseek-v4-pro
DEEPSEEK_BASE_URL=https://api.deepseek.com
MAX_EXTRACTED_CHARS=200000
LECTURE_BATCH_MAX_TOKENS=7500
ASSESSMENT_MAX_TOKENS=3000
SUMMARY_MAX_TOKENS=7000
GENERATED_FILES_DIR=generated
```

After replacing an earlier deployment, use **Manual Deploy → Clear build cache & deploy**.

## API flow

1. `POST /api/lecture-notes/jobs` extracts the outline and identifies course units.
2. `POST /api/lecture-notes/jobs/{job_id}/batches/{module_id}` generates one lecture unit and its practice assessment.
3. `POST /api/exports/docx` exports the assembled Markdown as a formatted Word document.
4. `POST /api/summaries/generate` creates a rich web and DOCX-ready summary.

## Tests

```bash
pytest -q
```
