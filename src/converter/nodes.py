from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Inline nodes
# ---------------------------------------------------------------------------

@dataclass
class Text:
    content: str


@dataclass
class Bold:
    children: list[InlineNode] = field(default_factory=list)


@dataclass
class Italic:
    children: list[InlineNode] = field(default_factory=list)


@dataclass
class Strikethrough:
    children: list[InlineNode] = field(default_factory=list)


@dataclass
class InlineCode:
    content: str


@dataclass
class Link:
    text: str
    url: str


@dataclass
class Image:
    url: str
    alt: str = ""


InlineNode = Text | Bold | Italic | Strikethrough | InlineCode | Link | Image


# ---------------------------------------------------------------------------
# Block nodes
# ---------------------------------------------------------------------------

@dataclass
class Paragraph:
    children: list[InlineNode] = field(default_factory=list)


@dataclass
class Heading:
    level: int
    children: list[InlineNode] = field(default_factory=list)


@dataclass
class CodeBlock:
    language: str
    content: str


@dataclass
class ListItem:
    children: list[InlineNode] = field(default_factory=list)
    sub_list: UnorderedList | OrderedList | None = None


@dataclass
class UnorderedList:
    items: list[ListItem] = field(default_factory=list)


@dataclass
class OrderedList:
    items: list[ListItem] = field(default_factory=list)


@dataclass
class Blockquote:
    children: list[InlineNode] = field(default_factory=list)


@dataclass
class HorizontalRule:
    pass


@dataclass
class TableCell:
    children: list[InlineNode] = field(default_factory=list)
    is_header: bool = False


@dataclass
class TableRow:
    cells: list[TableCell] = field(default_factory=list)


@dataclass
class Table:
    header_row: TableRow
    rows: list[TableRow] = field(default_factory=list)


BlockNode = (
    Heading
    | Paragraph
    | CodeBlock
    | UnorderedList
    | OrderedList
    | Blockquote
    | HorizontalRule
    | Table
)


@dataclass
class Document:
    children: list[BlockNode] = field(default_factory=list)
