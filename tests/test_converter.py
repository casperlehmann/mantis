"""Tests for the AST-based Jira/Markdown converter."""
from converter import jira_to_markdown, markdown_to_jira
from converter.nodes import (
    Blockquote,
    Bold,
    CodeBlock,
    Document,
    Heading,
    HorizontalRule,
    Image,
    InlineCode,
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
from converter.jira_parser import parse_jira
from converter.markdown_parser import parse_markdown
from converter.jira_renderer import render_jira
from converter.markdown_renderer import render_markdown


# ---------------------------------------------------------------------------
# TestJiraParser
# ---------------------------------------------------------------------------

class TestJiraParser:
    def test_heading_levels(self) -> None:
        for level in range(1, 7):
            doc = parse_jira(f'h{level}. Title')
            assert doc == Document(children=[
                Heading(level=level, children=[Text('Title')])
            ])

    def test_bold(self) -> None:
        doc = parse_jira('*bold text*')
        assert doc == Document(children=[
            Paragraph(children=[Bold(children=[Text('bold text')])])
        ])

    def test_italic(self) -> None:
        doc = parse_jira('_italic text_')
        assert doc == Document(children=[
            Paragraph(children=[Italic(children=[Text('italic text')])])
        ])

    def test_strikethrough(self) -> None:
        doc = parse_jira('Normal -struck- text')
        assert doc == Document(children=[
            Paragraph(children=[
                Text('Normal '),
                Strikethrough(children=[Text('struck')]),
                Text(' text'),
            ])
        ])

    def test_inline_code(self) -> None:
        doc = parse_jira('Some {{code here}} text')
        assert doc == Document(children=[
            Paragraph(children=[
                Text('Some '),
                InlineCode('code here'),
                Text(' text'),
            ])
        ])

    def test_code_block_with_language(self) -> None:
        doc = parse_jira('{code:python}\nprint("hi")\n{code}')
        assert doc == Document(children=[
            CodeBlock(language='python', content='print("hi")')
        ])

    def test_code_block_no_language(self) -> None:
        doc = parse_jira('{code}\nsome code\n{code}')
        assert doc == Document(children=[
            CodeBlock(language='', content='some code')
        ])

    def test_unordered_list(self) -> None:
        doc = parse_jira('* item1\n* item2')
        assert doc == Document(children=[
            UnorderedList(items=[
                ListItem(children=[Text('item1')]),
                ListItem(children=[Text('item2')]),
            ])
        ])

    def test_nested_unordered_list(self) -> None:
        doc = parse_jira('* parent\n** child')
        assert doc.children[0] == UnorderedList(items=[
            ListItem(
                children=[Text('parent')],
                sub_list=UnorderedList(items=[ListItem(children=[Text('child')])])
            )
        ])

    def test_ordered_list(self) -> None:
        doc = parse_jira('# item1\n# item2')
        assert doc == Document(children=[
            OrderedList(items=[
                ListItem(children=[Text('item1')]),
                ListItem(children=[Text('item2')]),
            ])
        ])

    def test_nested_ordered_list(self) -> None:
        doc = parse_jira('# parent\n## child')
        assert doc.children[0] == OrderedList(items=[
            ListItem(
                children=[Text('parent')],
                sub_list=OrderedList(items=[ListItem(children=[Text('child')])])
            )
        ])

    def test_link(self) -> None:
        doc = parse_jira('[Click here|http://example.com]')
        assert doc == Document(children=[
            Paragraph(children=[Link(text='Click here', url='http://example.com')])
        ])

    def test_image(self) -> None:
        doc = parse_jira('!screenshot.png!')
        assert doc == Document(children=[
            Paragraph(children=[Image(url='screenshot.png', alt='')])
        ])

    def test_blockquote(self) -> None:
        doc = parse_jira('bq. quoted text')
        assert doc == Document(children=[
            Blockquote(children=[Text('quoted text')])
        ])

    def test_horizontal_rule(self) -> None:
        doc = parse_jira('----')
        assert doc == Document(children=[HorizontalRule()])

    def test_table(self) -> None:
        doc = parse_jira('||Name||Age||\n|Alice|30|')
        assert len(doc.children) == 1
        table = doc.children[0]
        assert isinstance(table, Table)
        assert len(table.header_row.cells) == 2
        assert table.header_row.cells[0].is_header is True
        assert len(table.rows) == 1
        assert len(table.rows[0].cells) == 2

    def test_two_paragraphs(self) -> None:
        doc = parse_jira('first paragraph\n\nsecond paragraph')
        assert len(doc.children) == 2
        assert isinstance(doc.children[0], Paragraph)
        assert isinstance(doc.children[1], Paragraph)

    def test_mixed_inline(self) -> None:
        doc = parse_jira('Normal *bold* _italic_ text')
        para = doc.children[0]
        assert isinstance(para, Paragraph)
        assert Text('Normal ') in para.children
        assert Bold(children=[Text('bold')]) in para.children
        assert Italic(children=[Text('italic')]) in para.children

    def test_plain_text(self) -> None:
        doc = parse_jira('hello world')
        assert doc == Document(children=[
            Paragraph(children=[Text('hello world')])
        ])

    def test_empty_string(self) -> None:
        doc = parse_jira('')
        assert doc == Document(children=[])

    def test_code_block_preserves_markup(self) -> None:
        """Content inside code blocks should not be parsed as markup."""
        doc = parse_jira('{code}\n*not bold* h1. not heading\n{code}')
        assert doc == Document(children=[
            CodeBlock(language='', content='*not bold* h1. not heading')
        ])


# ---------------------------------------------------------------------------
# TestMarkdownParser
# ---------------------------------------------------------------------------

class TestMarkdownParser:
    def test_heading_levels(self) -> None:
        for level in range(1, 7):
            doc = parse_markdown(f'{"#" * level} Title')
            assert doc == Document(children=[
                Heading(level=level, children=[Text('Title')])
            ])

    def test_bold(self) -> None:
        doc = parse_markdown('*bold text*')
        assert doc == Document(children=[
            Paragraph(children=[Bold(children=[Text('bold text')])])
        ])

    def test_italic(self) -> None:
        doc = parse_markdown('_italic text_')
        assert doc == Document(children=[
            Paragraph(children=[Italic(children=[Text('italic text')])])
        ])

    def test_strikethrough(self) -> None:
        doc = parse_markdown('Normal ~~struck~~ text')
        assert doc == Document(children=[
            Paragraph(children=[
                Text('Normal '),
                Strikethrough(children=[Text('struck')]),
                Text(' text'),
            ])
        ])

    def test_inline_code(self) -> None:
        doc = parse_markdown('Some `code here` text')
        assert doc == Document(children=[
            Paragraph(children=[
                Text('Some '),
                InlineCode('code here'),
                Text(' text'),
            ])
        ])

    def test_code_block_with_language(self) -> None:
        doc = parse_markdown('```python\nprint("hi")\n```')
        assert doc == Document(children=[
            CodeBlock(language='python', content='print("hi")')
        ])

    def test_code_block_no_language(self) -> None:
        doc = parse_markdown('```\nsome code\n```')
        assert doc == Document(children=[
            CodeBlock(language='', content='some code')
        ])

    def test_unordered_list(self) -> None:
        doc = parse_markdown('- item1\n- item2')
        assert doc == Document(children=[
            UnorderedList(items=[
                ListItem(children=[Text('item1')]),
                ListItem(children=[Text('item2')]),
            ])
        ])

    def test_nested_unordered_list(self) -> None:
        doc = parse_markdown('- parent\n  - child')
        assert doc.children[0] == UnorderedList(items=[
            ListItem(
                children=[Text('parent')],
                sub_list=UnorderedList(items=[ListItem(children=[Text('child')])])
            )
        ])

    def test_ordered_list(self) -> None:
        doc = parse_markdown('1. item1\n2. item2')
        assert doc == Document(children=[
            OrderedList(items=[
                ListItem(children=[Text('item1')]),
                ListItem(children=[Text('item2')]),
            ])
        ])

    def test_link(self) -> None:
        doc = parse_markdown('[Click here](http://example.com)')
        assert doc == Document(children=[
            Paragraph(children=[Link(text='Click here', url='http://example.com')])
        ])

    def test_image(self) -> None:
        doc = parse_markdown('![alt text](screenshot.png)')
        assert doc == Document(children=[
            Paragraph(children=[Image(url='screenshot.png', alt='alt text')])
        ])

    def test_blockquote(self) -> None:
        doc = parse_markdown('> quoted text')
        assert doc == Document(children=[
            Blockquote(children=[Text('quoted text')])
        ])

    def test_horizontal_rule(self) -> None:
        doc = parse_markdown('---')
        assert doc == Document(children=[HorizontalRule()])

    def test_table(self) -> None:
        doc = parse_markdown('| Name | Age |\n| --- | --- |\n| Alice | 30 |')
        assert len(doc.children) == 1
        table = doc.children[0]
        assert isinstance(table, Table)
        assert len(table.header_row.cells) == 2
        assert table.header_row.cells[0].is_header is True
        assert len(table.rows) == 1

    def test_two_paragraphs(self) -> None:
        doc = parse_markdown('first paragraph\n\nsecond paragraph')
        assert len(doc.children) == 2
        assert isinstance(doc.children[0], Paragraph)
        assert isinstance(doc.children[1], Paragraph)

    def test_plain_text(self) -> None:
        doc = parse_markdown('hello world')
        assert doc == Document(children=[
            Paragraph(children=[Text('hello world')])
        ])

    def test_empty_string(self) -> None:
        doc = parse_markdown('')
        assert doc == Document(children=[])

    def test_code_block_preserves_markup(self) -> None:
        """Content inside fenced code blocks should not be parsed as markup."""
        doc = parse_markdown('```\n*not bold* # not heading\n```')
        assert doc == Document(children=[
            CodeBlock(language='', content='*not bold* # not heading')
        ])


# ---------------------------------------------------------------------------
# TestJiraRenderer
# ---------------------------------------------------------------------------

class TestJiraRenderer:
    def test_heading(self) -> None:
        doc = Document(children=[Heading(level=2, children=[Text('Title')])])
        assert render_jira(doc) == 'h2. Title'

    def test_paragraph(self) -> None:
        doc = Document(children=[Paragraph(children=[Text('hello')])])
        assert render_jira(doc) == 'hello'

    def test_bold(self) -> None:
        doc = Document(children=[Paragraph(children=[Bold(children=[Text('b')])])])
        assert render_jira(doc) == '*b*'

    def test_italic(self) -> None:
        doc = Document(children=[Paragraph(children=[Italic(children=[Text('i')])])])
        assert render_jira(doc) == '_i_'

    def test_strikethrough(self) -> None:
        doc = Document(children=[Paragraph(children=[Strikethrough(children=[Text('s')])])])
        assert render_jira(doc) == '-s-'

    def test_inline_code(self) -> None:
        doc = Document(children=[Paragraph(children=[InlineCode('foo')])])
        assert render_jira(doc) == '{{foo}}'

    def test_code_block_with_language(self) -> None:
        doc = Document(children=[CodeBlock(language='python', content='pass')])
        assert render_jira(doc) == '{code:python}\npass\n{code}'

    def test_code_block_no_language(self) -> None:
        doc = Document(children=[CodeBlock(language='', content='pass')])
        assert render_jira(doc) == '{code}\npass\n{code}'

    def test_unordered_list(self) -> None:
        doc = Document(children=[UnorderedList(items=[
            ListItem(children=[Text('a')]),
            ListItem(children=[Text('b')]),
        ])])
        assert render_jira(doc) == '* a\n* b'

    def test_nested_unordered_list(self) -> None:
        doc = Document(children=[UnorderedList(items=[
            ListItem(
                children=[Text('parent')],
                sub_list=UnorderedList(items=[ListItem(children=[Text('child')])])
            )
        ])])
        assert render_jira(doc) == '* parent\n** child'

    def test_ordered_list(self) -> None:
        doc = Document(children=[OrderedList(items=[
            ListItem(children=[Text('a')]),
            ListItem(children=[Text('b')]),
        ])])
        assert render_jira(doc) == '# a\n# b'

    def test_link(self) -> None:
        doc = Document(children=[Paragraph(children=[Link(text='here', url='http://x.com')])])
        assert render_jira(doc) == '[here|http://x.com]'

    def test_image(self) -> None:
        doc = Document(children=[Paragraph(children=[Image(url='img.png')])])
        assert render_jira(doc) == '!img.png!'

    def test_blockquote(self) -> None:
        doc = Document(children=[Blockquote(children=[Text('quote')])])
        assert render_jira(doc) == 'bq. quote'

    def test_horizontal_rule(self) -> None:
        doc = Document(children=[HorizontalRule()])
        assert render_jira(doc) == '----'

    def test_table(self) -> None:
        doc = Document(children=[Table(
            header_row=TableRow(cells=[
                TableCell(children=[Text('H1')], is_header=True),
                TableCell(children=[Text('H2')], is_header=True),
            ]),
            rows=[TableRow(cells=[
                TableCell(children=[Text('C1')]),
                TableCell(children=[Text('C2')]),
            ])]
        )])
        result = render_jira(doc)
        assert result == '||H1||H2||\n|C1|C2|'

    def test_multiple_blocks(self) -> None:
        doc = Document(children=[
            Heading(level=1, children=[Text('Title')]),
            Paragraph(children=[Text('body')]),
        ])
        assert render_jira(doc) == 'h1. Title\n\nbody'


# ---------------------------------------------------------------------------
# TestMarkdownRenderer
# ---------------------------------------------------------------------------

class TestMarkdownRenderer:
    def test_heading(self) -> None:
        doc = Document(children=[Heading(level=2, children=[Text('Title')])])
        assert render_markdown(doc) == '## Title'

    def test_paragraph(self) -> None:
        doc = Document(children=[Paragraph(children=[Text('hello')])])
        assert render_markdown(doc) == 'hello'

    def test_bold(self) -> None:
        doc = Document(children=[Paragraph(children=[Bold(children=[Text('b')])])])
        assert render_markdown(doc) == '*b*'

    def test_italic(self) -> None:
        doc = Document(children=[Paragraph(children=[Italic(children=[Text('i')])])])
        assert render_markdown(doc) == '_i_'

    def test_strikethrough(self) -> None:
        doc = Document(children=[Paragraph(children=[Strikethrough(children=[Text('s')])])])
        assert render_markdown(doc) == '~~s~~'

    def test_inline_code(self) -> None:
        doc = Document(children=[Paragraph(children=[InlineCode('foo')])])
        assert render_markdown(doc) == '`foo`'

    def test_code_block_with_language(self) -> None:
        doc = Document(children=[CodeBlock(language='python', content='pass')])
        assert render_markdown(doc) == '```python\npass\n```'

    def test_code_block_no_language(self) -> None:
        doc = Document(children=[CodeBlock(language='', content='pass')])
        assert render_markdown(doc) == '```\npass\n```'

    def test_unordered_list(self) -> None:
        doc = Document(children=[UnorderedList(items=[
            ListItem(children=[Text('a')]),
            ListItem(children=[Text('b')]),
        ])])
        assert render_markdown(doc) == '- a\n- b'

    def test_nested_unordered_list(self) -> None:
        doc = Document(children=[UnorderedList(items=[
            ListItem(
                children=[Text('parent')],
                sub_list=UnorderedList(items=[ListItem(children=[Text('child')])])
            )
        ])])
        assert render_markdown(doc) == '- parent\n  - child'

    def test_ordered_list(self) -> None:
        doc = Document(children=[OrderedList(items=[
            ListItem(children=[Text('a')]),
            ListItem(children=[Text('b')]),
        ])])
        assert render_markdown(doc) == '1. a\n1. b'

    def test_link(self) -> None:
        doc = Document(children=[Paragraph(children=[Link(text='here', url='http://x.com')])])
        assert render_markdown(doc) == '[here](http://x.com)'

    def test_image(self) -> None:
        doc = Document(children=[Paragraph(children=[Image(url='img.png', alt='')])])
        assert render_markdown(doc) == '![](img.png)'

    def test_blockquote(self) -> None:
        doc = Document(children=[Blockquote(children=[Text('quote')])])
        assert render_markdown(doc) == '> quote'

    def test_horizontal_rule(self) -> None:
        doc = Document(children=[HorizontalRule()])
        assert render_markdown(doc) == '---'

    def test_table(self) -> None:
        doc = Document(children=[Table(
            header_row=TableRow(cells=[
                TableCell(children=[Text('H1')], is_header=True),
                TableCell(children=[Text('H2')], is_header=True),
            ]),
            rows=[TableRow(cells=[
                TableCell(children=[Text('C1')]),
                TableCell(children=[Text('C2')]),
            ])]
        )])
        result = render_markdown(doc)
        assert result == '| H1 | H2 |\n| --- | --- |\n| C1 | C2 |'

    def test_multiple_blocks(self) -> None:
        doc = Document(children=[
            Heading(level=1, children=[Text('Title')]),
            Paragraph(children=[Text('body')]),
        ])
        assert render_markdown(doc) == '# Title\n\nbody'


# ---------------------------------------------------------------------------
# TestJiraToMarkdown  (end-to-end Jira -> Markdown)
# ---------------------------------------------------------------------------

class TestJiraToMarkdown:
    def test_headings(self) -> None:
        assert jira_to_markdown('h1. Biggest heading\n\nh2. Bigger heading') == \
            '# Biggest heading\n\n## Bigger heading'

    def test_inline_formatting(self) -> None:
        assert jira_to_markdown('Normal *bold* _italic_ text') == \
            'Normal *bold* _italic_ text'

    def test_full_example_from_tests(self) -> None:
        """Match the example used in the existing test_assistant.py."""
        result = jira_to_markdown(
            'h1. Biggest heading\n\nh2. Bigger heading\n\nNormal *bold* _italic_ text'
        )
        assert result == '# Biggest heading\n\n## Bigger heading\n\nNormal *bold* _italic_ text'

    def test_code_block(self) -> None:
        result = jira_to_markdown('{code:python}\nprint("hi")\n{code}')
        assert result == '```python\nprint("hi")\n```'

    def test_inline_code(self) -> None:
        assert jira_to_markdown('Use {{myFunc()}} here') == 'Use `myFunc()` here'

    def test_unordered_list(self) -> None:
        assert jira_to_markdown('* apple\n* banana') == '- apple\n- banana'

    def test_ordered_list(self) -> None:
        assert jira_to_markdown('# first\n# second') == '1. first\n1. second'

    def test_link(self) -> None:
        assert jira_to_markdown('[Jira|https://jira.example.com]') == \
            '[Jira](https://jira.example.com)'

    def test_image(self) -> None:
        assert jira_to_markdown('!logo.png!') == '![](logo.png)'

    def test_blockquote(self) -> None:
        assert jira_to_markdown('bq. This is a quote') == '> This is a quote'

    def test_horizontal_rule(self) -> None:
        assert jira_to_markdown('----') == '---'

    def test_strikethrough(self) -> None:
        assert jira_to_markdown('This is -struck- text') == 'This is ~~struck~~ text'

    def test_table(self) -> None:
        result = jira_to_markdown('||Name||Age||\n|Alice|30|')
        assert result == '| Name | Age |\n| --- | --- |\n| Alice | 30 |'

    def test_empty(self) -> None:
        assert jira_to_markdown('') == ''

    def test_multiline_code_block(self) -> None:
        jira = '{code:java}\npublic class Foo {\n    void bar() {}\n}\n{code}'
        md = jira_to_markdown(jira)
        assert md == '```java\npublic class Foo {\n    void bar() {}\n}\n```'


# ---------------------------------------------------------------------------
# TestMarkdownToJira  (end-to-end Markdown -> Jira)
# ---------------------------------------------------------------------------

class TestMarkdownToJira:
    def test_headings(self) -> None:
        assert markdown_to_jira('# Biggest heading\n\n## Bigger heading') == \
            'h1. Biggest heading\n\nh2. Bigger heading'

    def test_inline_formatting(self) -> None:
        assert markdown_to_jira('Normal *bold* _italic_ text') == \
            'Normal *bold* _italic_ text'

    def test_full_example_from_tests(self) -> None:
        """Mirror of the test_assistant.py example, going the other direction."""
        result = markdown_to_jira(
            '# Biggest heading\n\n## Bigger heading\n\nNormal *bold* _italic_ text'
        )
        assert result == 'h1. Biggest heading\n\nh2. Bigger heading\n\nNormal *bold* _italic_ text'

    def test_code_block(self) -> None:
        result = markdown_to_jira('```python\nprint("hi")\n```')
        assert result == '{code:python}\nprint("hi")\n{code}'

    def test_inline_code(self) -> None:
        assert markdown_to_jira('Use `myFunc()` here') == 'Use {{myFunc()}} here'

    def test_unordered_list(self) -> None:
        assert markdown_to_jira('- apple\n- banana') == '* apple\n* banana'

    def test_ordered_list(self) -> None:
        assert markdown_to_jira('1. first\n2. second') == '# first\n# second'

    def test_link(self) -> None:
        assert markdown_to_jira('[Jira](https://jira.example.com)') == \
            '[Jira|https://jira.example.com]'

    def test_image(self) -> None:
        assert markdown_to_jira('![alt](logo.png)') == '!logo.png|alt=alt!'

    def test_blockquote(self) -> None:
        assert markdown_to_jira('> This is a quote') == 'bq. This is a quote'

    def test_horizontal_rule(self) -> None:
        assert markdown_to_jira('---') == '----'

    def test_strikethrough(self) -> None:
        assert markdown_to_jira('This is ~~struck~~ text') == 'This is -struck- text'

    def test_table(self) -> None:
        result = markdown_to_jira('| Name | Age |\n| --- | --- |\n| Alice | 30 |')
        assert result == '||Name||Age||\n|Alice|30|'

    def test_empty(self) -> None:
        assert markdown_to_jira('') == ''

    def test_multiline_code_block(self) -> None:
        md = '```java\npublic class Foo {\n    void bar() {}\n}\n```'
        jira = markdown_to_jira(md)
        assert jira == '{code:java}\npublic class Foo {\n    void bar() {}\n}\n{code}'


# ---------------------------------------------------------------------------
# TestRoundtrip
# ---------------------------------------------------------------------------

class TestRoundtrip:
    def test_jira_to_md_to_jira_headings(self) -> None:
        original = 'h1. Title\n\nh2. Subtitle'
        assert markdown_to_jira(jira_to_markdown(original)) == original

    def test_jira_to_md_to_jira_inline(self) -> None:
        original = 'Normal *bold* _italic_ text'
        assert markdown_to_jira(jira_to_markdown(original)) == original

    def test_jira_to_md_to_jira_code_block(self) -> None:
        original = '{code:python}\npass\n{code}'
        assert markdown_to_jira(jira_to_markdown(original)) == original

    def test_jira_to_md_to_jira_list(self) -> None:
        original = '* a\n* b'
        assert markdown_to_jira(jira_to_markdown(original)) == original

    def test_jira_to_md_to_jira_link(self) -> None:
        original = '[text|http://example.com]'
        assert markdown_to_jira(jira_to_markdown(original)) == original

    def test_jira_to_md_to_jira_hr(self) -> None:
        original = '----'
        assert markdown_to_jira(jira_to_markdown(original)) == original

    def test_jira_to_md_to_jira_table(self) -> None:
        original = '||Name||Age||\n|Alice|30|'
        assert markdown_to_jira(jira_to_markdown(original)) == original

    def test_md_to_jira_to_md_headings(self) -> None:
        original = '# Title\n\n## Subtitle'
        assert jira_to_markdown(markdown_to_jira(original)) == original

    def test_md_to_jira_to_md_inline(self) -> None:
        original = 'Normal *bold* _italic_ text'
        assert jira_to_markdown(markdown_to_jira(original)) == original

    def test_md_to_jira_to_md_code_block(self) -> None:
        original = '```python\npass\n```'
        assert jira_to_markdown(markdown_to_jira(original)) == original

    def test_md_to_jira_to_md_list(self) -> None:
        original = '- a\n- b'
        assert jira_to_markdown(markdown_to_jira(original)) == original

    def test_md_to_jira_to_md_link(self) -> None:
        original = '[text](http://example.com)'
        assert jira_to_markdown(markdown_to_jira(original)) == original

    def test_md_to_jira_to_md_hr(self) -> None:
        original = '---'
        assert jira_to_markdown(markdown_to_jira(original)) == original

    def test_md_to_jira_to_md_table(self) -> None:
        original = '| Name | Age |\n| --- | --- |\n| Alice | 30 |'
        assert jira_to_markdown(markdown_to_jira(original)) == original

    def test_complex_document_jira_to_md_to_jira(self) -> None:
        original = (
            'h1. Project Overview\n\n'
            'This is the *main* description.\n\n'
            '* Feature A\n'
            '* Feature B\n\n'
            '{code:python}\nprint("hello")\n{code}\n\n'
            '----\n\n'
            'bq. Important note'
        )
        assert markdown_to_jira(jira_to_markdown(original)) == original
