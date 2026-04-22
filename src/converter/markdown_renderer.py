"""Render an AST to Markdown."""
from __future__ import annotations

from converter.nodes import (
    Blockquote,
    Bold,
    CodeBlock,
    Document,
    Heading,
    HorizontalRule,
    Image,
    InlineCode,
    InlineNode,
    Italic,
    Link,
    ListItem,
    OrderedList,
    Paragraph,
    Strikethrough,
    Table,
    Text,
    UnorderedList,
)


def _render_inline(nodes: list[InlineNode]) -> str:
    parts: list[str] = []
    for node in nodes:
        match node:
            case Text(content=c):
                parts.append(c)
            case Bold(children=ch):
                parts.append(f'*{_render_inline(ch)}*')
            case Italic(children=ch):
                parts.append(f'_{_render_inline(ch)}_')
            case Strikethrough(children=ch):
                parts.append(f'~~{_render_inline(ch)}~~')
            case InlineCode(content=c):
                parts.append(f'`{c}`')
            case Link(text=t, url=u):
                parts.append(f'[{t}]({u})')
            case Image(url=u, alt=a):
                parts.append(f'![{a}]({u})')
    return ''.join(parts)


def _render_list_items(
    items: list[ListItem], marker: str, indent: str = ''
) -> list[str]:
    lines: list[str] = []
    for item in items:
        lines.append(f'{indent}{marker} {_render_inline(item.children)}')
        if item.sub_list is not None:
            sub = item.sub_list
            child_indent = indent + '  '
            if isinstance(sub, UnorderedList):
                lines.extend(_render_list_items(sub.items, '-', child_indent))
            elif isinstance(sub, OrderedList):
                lines.extend(_render_list_items(sub.items, '1.', child_indent))
    return lines


def render_markdown(doc: Document) -> str:
    """Render a Document AST to Markdown text."""
    block_parts: list[str] = []

    for block in doc.children:
        match block:
            case Heading(level=lvl, children=ch):
                block_parts.append(f'{"#" * lvl} {_render_inline(ch)}')

            case Paragraph(children=ch):
                block_parts.append(_render_inline(ch))

            case CodeBlock(language=lang, content=content):
                fence = f'```{lang}' if lang else '```'
                block_parts.append(f'{fence}\n{content}\n```')

            case UnorderedList(items=items):
                block_parts.append('\n'.join(_render_list_items(items, '-')))

            case OrderedList(items=items):
                block_parts.append('\n'.join(_render_list_items(items, '1.')))

            case Blockquote(children=ch):
                block_parts.append(f'> {_render_inline(ch)}')

            case HorizontalRule():
                block_parts.append('---')

            case Table(header_row=header, rows=rows):
                header_cells = [
                    _render_inline(cell.children) for cell in header.cells
                ]
                sep = ['---'] * len(header_cells)
                md_rows: list[str] = []
                md_rows.append('| ' + ' | '.join(header_cells) + ' |')
                md_rows.append('| ' + ' | '.join(sep) + ' |')
                for row in rows:
                    row_cells = [_render_inline(cell.children) for cell in row.cells]
                    md_rows.append('| ' + ' | '.join(row_cells) + ' |')
                block_parts.append('\n'.join(md_rows))

    return '\n\n'.join(block_parts)
