"""Parse Jira wiki markup into an AST."""
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

# Patterns ordered by precedence; each group name maps to a node type.
_INLINE_RE = re.compile(
    r'(?P<inline_code>\{\{(?P<ic_content>.*?)\}\})'          # {{...}}
    r'|(?P<bold>\*(?P<b_content>[^*]+)\*)'                    # *...*
    r'|(?P<italic>_(?P<i_content>[^_]+)_)'                    # _..._
    r'|(?P<strike>(?<!\w)-(?P<s_content>[^\s-][^-]*[^\s-])-(?!\w))'  # -...-
    r'|(?P<image>!(?P<img_url>[^!\s|]+)(?:\|[^!]*)?\!)'      # !url!
    r'|(?P<link>\[(?P<l_text>[^\]|]+)\|(?P<l_url>[^\]]+)\])' # [text|url]
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
        elif m.group('bold'):
            nodes.append(Bold(_parse_inline(m.group('b_content'))))
        elif m.group('italic'):
            nodes.append(Italic(_parse_inline(m.group('i_content'))))
        elif m.group('strike'):
            nodes.append(Strikethrough(_parse_inline(m.group('s_content'))))
        elif m.group('image'):
            nodes.append(Image(url=m.group('img_url')))
        elif m.group('link'):
            nodes.append(Link(text=m.group('l_text'), url=m.group('l_url')))
        pos = end
    if pos < len(text):
        nodes.append(Text(text[pos:]))
    return nodes


# ---------------------------------------------------------------------------
# Block parsing helpers
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r'^h([1-6])\. (.*)$')
_HR_RE = re.compile(r'^-{4,}$')
_BQ_RE = re.compile(r'^bq\. (.*)$')
_CODE_OPEN_RE = re.compile(r'^\{code(?::([^}]*))?\}$')
_CODE_CLOSE_RE = re.compile(r'^\{code\}$')
_TABLE_HEADER_RE = re.compile(r'^\|\|')
_TABLE_ROW_RE = re.compile(r'^\|(?!\|)')
_ULIST_RE = re.compile(r'^(\*+) (.+)$')
_OLIST_RE = re.compile(r'^(#+) (.+)$')


def _parse_jira_table_header(line: str) -> TableRow:
    """Parse a Jira table header row: ||h1||h2||"""
    parts = re.split(r'\|\|', line)
    cells = [
        TableCell(children=_parse_inline(p.strip()), is_header=True)
        for p in parts
        if p.strip()
    ]
    return TableRow(cells=cells)


def _parse_jira_table_row(line: str) -> TableRow:
    """Parse a Jira table data row: |c1|c2|"""
    parts = line.split('|')
    cells = [
        TableCell(children=_parse_inline(p.strip()), is_header=False)
        for p in parts
        if p.strip()
    ]
    return TableRow(cells=cells)


def _parse_list_lines(
    lines: list[str], start: int, list_char: str
) -> tuple[UnorderedList | OrderedList, int]:
    """
    Parse consecutive list lines starting at `start`.
    `list_char` is '*' for unordered or '#' for ordered.
    Returns (list_node, next_line_index).
    """
    pattern = re.compile(rf'^(\{list_char}+) (.+)$' if list_char == '*' else r'^(#+) (.+)$')
    items: list[ListItem] = []
    i = start

    while i < len(lines):
        m = pattern.match(lines[i])
        if not m:
            break
        depth = len(m.group(1))
        if depth > 1:
            # This is a nested item — caller handles it via sub_list
            break
        content = m.group(2)
        item = ListItem(children=_parse_inline(content))
        i += 1

        # Look ahead for nested items
        if i < len(lines):
            nested_m = pattern.match(lines[i])
            if nested_m and len(nested_m.group(1)) > 1:
                # Build sub-list by stripping one level of list marker
                sub_lines = []
                while i < len(lines):
                    nm = pattern.match(lines[i])
                    if not nm or len(nm.group(1)) <= 1:
                        break
                    # Strip one marker character from the beginning
                    stripped = lines[i][1:]
                    sub_lines.append(stripped)
                    i += 1
                sub_list, _ = _parse_list_lines(sub_lines, 0, list_char)
                item.sub_list = sub_list

        items.append(item)

    if list_char == '*':
        return UnorderedList(items=items), i
    else:
        return OrderedList(items=items), i


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_jira(text: str) -> Document:
    """Parse Jira wiki markup into a Document AST."""
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

        # --- Code block ---
        m_code = _CODE_OPEN_RE.match(line)
        if m_code:
            flush_paragraph()
            language = m_code.group(1) or ''
            i += 1
            code_lines: list[str] = []
            while i < len(lines):
                if _CODE_CLOSE_RE.match(lines[i]):
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
                level=int(m_h.group(1)),
                children=_parse_inline(m_h.group(2))
            ))
            i += 1
            continue

        # --- Horizontal rule ---
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

        # --- Table header ---
        if _TABLE_HEADER_RE.match(line):
            flush_paragraph()
            header_row = _parse_jira_table_header(line)
            data_rows: list[TableRow] = []
            i += 1
            while i < len(lines) and _TABLE_ROW_RE.match(lines[i]):
                data_rows.append(_parse_jira_table_row(lines[i]))
                i += 1
            blocks.append(Table(header_row=header_row, rows=data_rows))
            continue

        # --- Unordered list ---
        m_ul = _ULIST_RE.match(line)
        if m_ul:
            flush_paragraph()
            ul, i = _parse_list_lines(lines, i, '*')
            blocks.append(ul)
            continue

        # --- Ordered list ---
        m_ol = _OLIST_RE.match(line)
        if m_ol:
            flush_paragraph()
            ol, i = _parse_list_lines(lines, i, '#')
            blocks.append(ol)
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
