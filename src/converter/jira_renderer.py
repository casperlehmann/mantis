"""Render an AST to Jira wiki markup."""
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
                parts.append(f'-{_render_inline(ch)}-')
            case InlineCode(content=c):
                parts.append('{{' + c + '}}')
            case Link(text=t, url=u):
                parts.append(f'[{t}|{u}]')
            case Image(url=u, alt=a):
                if a:
                    parts.append(f'!{u}|alt={a}!')
                else:
                    parts.append(f'!{u}!')
    return ''.join(parts)


def _render_list_items(
    items: list[ListItem], marker: str, depth: int = 1
) -> list[str]:
    prefix = marker * depth
    lines: list[str] = []
    for item in items:
        lines.append(f'{prefix} {_render_inline(item.children)}')
        if item.sub_list is not None:
            sub = item.sub_list
            if isinstance(sub, UnorderedList):
                lines.extend(_render_list_items(sub.items, '*', depth + 1))
            elif isinstance(sub, OrderedList):
                lines.extend(_render_list_items(sub.items, '#', depth + 1))
    return lines


def render_jira(doc: Document) -> str:
    """Render a Document AST to Jira wiki markup text."""
    block_parts: list[str] = []

    for block in doc.children:
        match block:
            case Heading(level=lvl, children=ch):
                block_parts.append(f'h{lvl}. {_render_inline(ch)}')

            case Paragraph(children=ch):
                block_parts.append(_render_inline(ch))

            case CodeBlock(language=lang, content=content):
                if lang:
                    block_parts.append(f'{{code:{lang}}}\n{content}\n{{code}}')
                else:
                    block_parts.append(f'{{code}}\n{content}\n{{code}}')

            case UnorderedList(items=items):
                block_parts.append('\n'.join(_render_list_items(items, '*')))

            case OrderedList(items=items):
                block_parts.append('\n'.join(_render_list_items(items, '#')))

            case Blockquote(children=ch):
                block_parts.append(f'bq. {_render_inline(ch)}')

            case HorizontalRule():
                block_parts.append('----')

            case Table(header_row=header, rows=rows):
                jira_rows: list[str] = []
                header_cells = '||' + '||'.join(
                    _render_inline(cell.children) for cell in header.cells
                ) + '||'
                jira_rows.append(header_cells)
                for row in rows:
                    row_cells = '|' + '|'.join(
                        _render_inline(cell.children) for cell in row.cells
                    ) + '|'
                    jira_rows.append(row_cells)
                block_parts.append('\n'.join(jira_rows))

    return '\n\n'.join(block_parts)
