"""AST-based bidirectional converter between Jira wiki markup and Markdown."""
from converter.nodes import Document
from converter.jira_parser import parse_jira
from converter.markdown_parser import parse_markdown
from converter.jira_renderer import render_jira
from converter.markdown_renderer import render_markdown

__all__ = [
    "jira_to_markdown",
    "markdown_to_jira",
    "parse_jira",
    "parse_markdown",
    "render_jira",
    "render_markdown",
    "Document",
]


def jira_to_markdown(text: str) -> str:
    """Convert Jira wiki markup to Markdown."""
    doc = parse_jira(text)
    return render_markdown(doc)


def markdown_to_jira(text: str) -> str:
    """Convert Markdown to Jira wiki markup."""
    doc = parse_markdown(text)
    return render_jira(doc)
