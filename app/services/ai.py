import json
import re
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
                timeout=210.0,
                max_retries=2,
            )

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        system: str | None = None,
    ) -> str:
        if not self.client:
            return self._development_preview(prompt)

        response = self.client.chat.completions.create(
            model=self.settings.deepseek_model,
            messages=[
                {
                    "role": "system",
                    "content": system
                    or (
                        "You are an expert academic writer and curriculum developer. "
                        "Produce accurate, source-grounded educational content in formal "
                        "British English. Never fabricate references, facts, statistics, "
                        "authors, quotations, laws, policies or source details."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

        text = response.choices[0].message.content
        if not text or not text.strip():
            raise RuntimeError("The AI service returned an empty response.")
        return text.strip()

    def generate_json(
        self,
        prompt: str,
        *,
        max_tokens: int,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        if not self.client:
            return {}
        text = self.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system=(
                "Return only valid JSON matching the requested schema. Do not use Markdown "
                "code fences or add commentary. Do not invent information beyond the supplied notes."
            ),
        )
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I | re.S)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start >= 0 and end > start:
                return json.loads(cleaned[start : end + 1])
            raise RuntimeError("The AI assessment response was not valid JSON.")

    @staticmethod
    def _development_preview(prompt: str) -> str:
        preview = prompt[:2_500]
        return (
            "# Development Preview\n\n"
            "AI generation is disabled because `DEEPSEEK_API_KEY` has not been configured. "
            "The batching, extraction and rendering pipeline is working.\n\n"
            "## Prompt preview\n\n"
            f"```text\n{preview}\n```"
        )
