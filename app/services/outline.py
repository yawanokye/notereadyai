import math
import re
from dataclasses import dataclass


_EXPLICIT = re.compile(
    r"^(?:#{1,4}\s*)?(week|unit|module|topic|period|lecture)\s+"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen)"
    r"\s*[:.\-–—]?\s*(.*)$",
    re.IGNORECASE,
)
_NUMBERED = re.compile(r"^(?:#{1,4}\s*)?\d{1,2}[.)]\s+(.{4,100})$")
_MARKDOWN_HEADING = re.compile(r"^#{1,3}\s+(.{4,120})$")
_SKIP = {
    "learning outcomes",
    "course objectives",
    "assessment",
    "references",
    "recommended readings",
    "introduction",
    "course description",
}


@dataclass(slots=True)
class ModuleSlice:
    id: str
    sequence: int
    title: str
    source_text: str


def _clean_title(line: str) -> str:
    value = re.sub(r"^#{1,6}\s*", "", line).strip()
    value = re.sub(r"\s+", " ", value)
    return value.strip(" :-–—")


def _candidate_heading(line: str) -> tuple[int, str] | None:
    stripped = line.strip()
    if not stripped or len(stripped) > 150:
        return None

    explicit = _EXPLICIT.match(stripped)
    if explicit:
        title = _clean_title(stripped)
        return 3, title

    markdown = _MARKDOWN_HEADING.match(stripped)
    if markdown:
        title = _clean_title(markdown.group(1))
        if title.lower() not in _SKIP:
            return 2, title

    numbered = _NUMBERED.match(stripped)
    if numbered:
        title = _clean_title(numbered.group(1))
        if title.lower() not in _SKIP:
            return 1, title

    if stripped.isupper() and 5 <= len(stripped) <= 100 and stripped.lower() not in _SKIP:
        return 1, _clean_title(stripped)

    return None


def derive_modules(source_text: str, teaching_weeks: int) -> list[ModuleSlice]:
    lines = source_text.splitlines()
    candidates: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        found = _candidate_heading(line)
        if found:
            priority, title = found
            if not candidates or title.casefold() != candidates[-1][2].casefold():
                candidates.append((index, priority, title))

    explicit = [item for item in candidates if item[1] == 3]
    structural = [item for item in candidates if item[1] >= 2]
    if len(explicit) >= 2:
        selected = explicit
    elif len(structural) >= 2:
        selected = structural
    else:
        selected = candidates

    # Prevent a detailed source from becoming dozens of tiny batches.
    max_modules = max(1, min(teaching_weeks, 18))
    if len(selected) > max_modules:
        selected = _group_headings(selected, max_modules)

    if len(selected) >= 2:
        modules: list[ModuleSlice] = []
        for position, (start, _priority, title) in enumerate(selected):
            end = selected[position + 1][0] if position + 1 < len(selected) else len(lines)
            excerpt = "\n".join(lines[start:end]).strip()
            modules.append(
                ModuleSlice(
                    id=f"unit-{len(modules) + 1}",
                    sequence=len(modules) + 1,
                    title=title,
                    source_text=excerpt,
                )
            )
        if modules:
            return modules

    return _chunk_fallback(source_text, max_modules)


def _group_headings(
    headings: list[tuple[int, int, str]], max_modules: int
) -> list[tuple[int, int, str]]:
    step = len(headings) / max_modules
    selected: list[tuple[int, int, str]] = []
    for group_index in range(max_modules):
        index = min(len(headings) - 1, math.floor(group_index * step))
        item = headings[index]
        if not selected or item[0] != selected[-1][0]:
            selected.append(item)
    return selected


def _chunk_fallback(source_text: str, max_modules: int) -> list[ModuleSlice]:
    target_size = 8_000
    count = max(1, min(max_modules, math.ceil(len(source_text) / target_size)))
    chunk_size = math.ceil(len(source_text) / count)
    modules: list[ModuleSlice] = []
    for index in range(count):
        start = index * chunk_size
        end = min(len(source_text), (index + 1) * chunk_size)
        excerpt = source_text[start:end].strip()
        if excerpt:
            modules.append(
                ModuleSlice(
                    id=f"unit-{index + 1}",
                    sequence=index + 1,
                    title=f"Course Unit {index + 1}",
                    source_text=excerpt,
                )
            )
    return modules
