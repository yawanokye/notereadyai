from typing import Any

from app.config import Settings

try:
    from openai import OpenAI
except ImportError:  # Lets development-preview mode run before dependencies are installed.
    OpenAI = None  # type: ignore[assignment]


class AIService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client: Any = None
        if settings.ai_enabled:
            if OpenAI is None:
                raise RuntimeError(
                    "The openai package is not installed. Run `pip install -r requirements.txt`."
                )
            self.client = OpenAI(api_key=settings.openai_api_key)

    def generate(self, prompt: str) -> str:
        if not self.client or not self.settings.openai_model:
            return self._development_preview(prompt)

        response = self.client.responses.create(
            model=self.settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Produce accurate, source-grounded educational content. "
                        "Never fabricate references, facts or source details."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        text = response.output_text.strip()
        if not text:
            raise RuntimeError("The AI service returned an empty response.")
        return text

    @staticmethod
    def _development_preview(prompt: str) -> str:
        preview = prompt[:2_500]
        return (
            "# Development Preview\n\n"
            "AI generation is disabled because `OPENAI_API_KEY` or `OPENAI_MODEL` "
            "has not been configured. The extraction and request pipeline is working.\n\n"
            "## Prompt preview\n\n"
            f"```text\n{preview}\n```\n\n"
            "Configure the two environment variables to generate the full output."
        )
