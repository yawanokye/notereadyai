from markdown_it import MarkdownIt


_MD = (
    MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})
    .enable("table")
    .enable("strikethrough")
)


def render_markdown(markdown_text: str) -> str:
    """Render generated Markdown safely. Raw HTML is disabled."""
    return _MD.render(markdown_text)


def markdown_parser() -> MarkdownIt:
    return _MD
