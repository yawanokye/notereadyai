from fastapi.testclient import TestClient

from app.main import app


def test_lecture_notes_preview() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/lecture-notes/generate",
        data={
            "academic_level": "Undergraduate Level 100",
            "course_title": "Principles of Procurement",
            "course_code": "PCM 102",
            "credit_hours": "3",
            "teaching_weeks": "13",
            "contact_hours_per_week": "3",
            "citation_style": "APA 7th edition",
            "context_preference": "Use Ghanaian examples where relevant.",
        },
        files={"file": ("outline.txt", b"Week 1: Introduction to procurement", "text/plain")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Principles of Procurement Lecture Notes"
    assert payload["ai_enabled"] is False
    assert "Development Preview" in payload["content_markdown"]


def test_docx_export() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/exports/docx",
        json={"title": "Sample Notes", "content_markdown": "# Topic\n\n- Point one"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
