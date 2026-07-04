from typing import Any

from app.config import Settings

try:
    from openai import OpenAI
except ImportError:  # Allows preview mode before dependencies are installed.
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

            self.client = OpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                timeout=180.0,
                max_retries=2,
            )

    def generate(self, prompt: str) -> str:
        if not self.client:
            return self._development_preview(prompt)

        response = self.client.chat.completions.create(
            model=self.settings.deepseek_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Produce accurate, source-grounded educational content. "
                        "Follow the uploaded material closely. Never fabricate references, "
                        "facts, statistics, authors, quotations, or source details. "
                        "Write in clear formal British English."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )

        text = response.choices[0].message.content
        if not text or not text.strip():
            raise RuntimeError("The AI service returned an empty response.")

        return text.strip()

    @staticmethod
    def _development_preview(prompt: str) -> str:
        preview = prompt[:2_500]
        return (
            "# Development Preview\n\n"
            "AI generation is disabled because `DEEPSEEK_API_KEY` has not been "
            "configured. The extraction and request pipeline is working.\n\n"
            "## Prompt preview\n\n"
            f"```text\n{preview}\n```\n\n"
            "Configure the DeepSeek environment variables to generate the full output."
        )
