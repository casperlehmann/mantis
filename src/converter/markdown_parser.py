"""Parse Markdown into an AST."""
from __future__ import annotations

import re

from converter.nodes import (
    BlockNode,
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
    TableCell,
    TableRow,
    Text,
    UnorderedList,
)

# ---------------------------------------------------------------------------
# Inline parsing
# ---------------------------------------------------------------------------

_INLINE_RE = re.compile(
    r'(?P<inline_code>`(?P<ic_content>[^`]+)`)'             # `...`
    r'|(?P<image>!\[(?P<img_alt>[^\]]*)\]\((?P<img_url>[^)]+)\))'  # ![alt](url)
    r'|(?P<link>\[(?P<l_text>[^\]]+)\]\((?P<l_url>[^)]+)\))'       # [text](url)
    r'|(?P<strike>~~(?P<s_content>.+?)~~)'                  # ~~...~~
    r'|(?P<bold>\*(?P<b_content>[^*]+)\*)'                  # *...*
    r'|(?P<italic>_(?P<i_content>[^_]+)_)'                  # _..._
)


def _parse_inline(text: str) -> list[InlineNode]:
    nodes: list[InlineNode] = []
    pos = 0
    for m in _INLINE_RE.finditer(text):
        start, end = m.span()
        if start > pos:
            nodes.append(Text(text[pos:start]))
        if m.group('inline_code'):
            nodes.append(InlineCode(m.group('ic_content')))
        elif m.group('image'):
            nodes.append(Image(url=m.group('img_url'), alt=m.group('img_alt')))
        elif m.group('link'):
            nodes.append(Link(text=m.group('l_text'), url=m.group('l_url')))
        elif m.group('strike'):
            nodes.append(Strikethrough(_parse_inline(m.group('s_content'))))
        elif m.group('bold'):
            nodes.append(Bold(_parse_inline(m.group('b_content'))))
        elif m.group('italic'):
            nodes.append(Italic(_parse_inline(m.group('i_content'))))
        pos = end
    if pos < len(text):
        nodes.append(Text(text[pos:]))
    return nodes


# ---------------------------------------------------------------------------
# Block parsing helpers
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r'^(#{1,6}) (.+)$')
_HR_RE = re.compile(r'^(-{3,}|\*{3,}|_{3,})$')
_BQ_RE = re.compile(r'^> (.*)$')
_FENCE_OPEN_RE = re.compile(r'^```(.*)$')
_FENCE_CLOSE_RE = re.compile(r'^```\s*$')
_TABLE_ROW_RE = re.compile(r'^\|')
_TABLE_SEP_RE = re.compile(r'^\|[\s|:-]+\|$')
_ULIST_RE = re.compile(r'^( *)[-*] (.+)$')
_OLIST_RE = re.compile(r'^( *)\d+\. (.+)$')


def _parse_md_table(lines: list[str], start: int) -> tuple[Table | None, int]:
    """Try to parse a Markdown table starting at start. Returns (Table, next_i) or (None, start)."""
    i = start
    if i >= len(lines) or not _TABLE_ROW_RE.match(lines[i]):
        return None, start

    header_line = lines[i]
    i += 1

    # Next line must be separator
    if i >= len(lines) or not _TABLE_SEP_RE.match(lines[i]):
        return None, start
    i += 1  # skip separator

    # Parse header cells
    header_parts = [p.strip() for p in header_line.split('|') if p.strip()]
    header_cells = [
        TableCell(children=_parse_inline(p), is_header=True)
        for p in header_parts
    ]
    header_row = TableRow(cells=header_cells)

    data_rows: list[TableRow] = []
    while i < len(lines) and _TABLE_ROW_RE.match(lines[i]):
        parts = [p.strip() for p in lines[i].split('|') if p.strip()]
        cells = [TableCell(children=_parse_inline(p)) for p in parts]
        data_rows.append(TableRow(cells=cells))
        i += 1

    return Table(header_row=header_row, rows=data_rows), i


def _parse_list_block(
    lines: list[str], start: int
) -> tuple[UnorderedList | OrderedList | None, int]:
    """
    Parse a list block (unordered or ordered) starting at start.
    Handles nesting via indentation.
    """
    i = start
    if i >= len(lines):
        return None, start

    m_u = _ULIST_RE.match(lines[i])
    m_o = _OLIST_RE.match(lines[i])
    if not (m_u or m_o):
        return None, start

    is_ordered = bool(m_o)
    base_indent = len((m_o or m_u).group(1))  # type: ignore[union-attr]

    items: list[ListItem] = []

    while i < len(lines):
        m = _OLIST_RE.match(lines[i]) if is_ordered else _ULIST_RE.match(lines[i])
        if not m:
            break
        indent = len(m.group(1))
        if indent != base_indent:
            break

        content = m.group(2)
        item = ListItem(children=_parse_inline(content))
        i += 1

        # Check for nested list
        if i < len(lines):
            nm_u = _ULIST_RE.match(lines[i])
            nm_o = _OLIST_RE.match(lines[i])
            nm = nm_o if is_ordered else nm_u
            if nm and len(nm.group(1)) > base_indent:
                sub_list, i = _parse_list_block(lines, i)
                item.sub_list = sub_list

        items.append(item)

    if is_ordered:
        return OrderedList(items=items), i
    else:
        return UnorderedList(items=items), i


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_markdown(text: str) -> Document:
    """Parse Markdown text into a Document AST."""
    lines = text.split('\n')
    blocks: list[BlockNode] = []
    i = 0
    para_lines: list[str] = []

    def flush_paragraph() -> None:
        if para_lines:
            combined = ' '.join(para_lines).strip()
            if combined:
                blocks.append(Paragraph(children=_parse_inline(combined)))
            para_lines.clear()

    while i < len(lines):
        line = lines[i]

        # --- Fenced code block ---
        m_fence = _FENCE_OPEN_RE.match(line)
        if m_fence:
            flush_paragraph()
            language = m_fence.group(1).strip()
            i += 1
            code_lines: list[str] = []
            while i < len(lines):
                if _FENCE_CLOSE_RE.match(lines[i]):
                    i += 1
                    break
                code_lines.append(lines[i])
                i += 1
            blocks.append(CodeBlock(language=language, content='\n'.join(code_lines)))
            continue

        # --- Heading ---
        m_h = _HEADING_RE.match(line)
        if m_h:
            flush_paragraph()
            blocks.append(Heading(
                level=len(m_h.group(1)),
                children=_parse_inline(m_h.group(2))
            ))
            i += 1
            continue

        # --- Horizontal rule (must check before list to avoid --- being a list) ---
        if _HR_RE.match(line):
            flush_paragraph()
            blocks.append(HorizontalRule())
            i += 1
            continue

        # --- Blockquote ---
        m_bq = _BQ_RE.match(line)
        if m_bq:
            flush_paragraph()
            blocks.append(Blockquote(children=_parse_inline(m_bq.group(1))))
            i += 1
            continue

        # --- Table ---
        if _TABLE_ROW_RE.match(line):
            flush_paragraph()
            table, new_i = _parse_md_table(lines, i)
            if table is not None:
                blocks.append(table)
                i = new_i
                continue
            # Not a valid table — fall through to paragraph

        # --- List ---
        if _ULIST_RE.match(line) or _OLIST_RE.match(line):
            flush_paragraph()
            lst, i = _parse_list_block(lines, i)
            if lst is not None:
                blocks.append(lst)
            continue

        # --- Empty line: paragraph break ---
        if line.strip() == '':
            flush_paragraph()
            i += 1
            continue

        # --- Paragraph text ---
        para_lines.append(line)
        i += 1

    flush_paragraph()
    return Document(children=blocks)
