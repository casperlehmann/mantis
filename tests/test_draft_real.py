import pytest
from src.drafts.draft import Draft

class DummyMantis:
    drafts_dir = None
    options = type('opt', (), {'chat_gpt_activated': False})()
    assistant = None
class DummyIssue:
    def get_field(self, key, default=None):
        return 'summary-value' if key == 'summary' else default
    def get(self, key):
        return 'KEY-1'

# This test will import and instantiate the real Draft class, but will fail if drafts_dir is not a Path.
def test_real_draft_import(tmp_path):
    mantis = DummyMantis()
    mantis.drafts_dir = tmp_path
    issue = DummyIssue()
    # Patch template_md.template to minimal frontmatter for test
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    draft = Draft(mantis, issue)
    assert draft.summary == 'summary-value'
    assert draft.key == 'KEY-1'
    assert draft.draft_path.exists()
    assert 'summary-value' in draft.raw_draft

def test_j2m_identity():
    from src.drafts.draft import j2m
    assert j2m("foo") == "foo"

def test_generate_frontmatter_true_false(tmp_path, monkeypatch):
    from src.drafts.draft import Draft
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = None
    class Issue:
        def get_field(self, key, default=None):
            if key == 'summary': return 'summary-value'
            if key == 'header': return 'True'
            return default
        def get(self, key): return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: True\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    draft = Draft(Mantis(), Issue())
    # The header is always set to the formatted header, not the string 'True'
    assert draft.template.metadata['header'] == '[KEY-1] summary-value'

def test_generate_body_with_chatgpt(tmp_path, monkeypatch):
    from src.drafts.draft import Draft
    class Assistant:
        TextFormat = type('TF', (), {'MARKDOWN': 'Markdown'})
        def convert_text_format(self, input_text, target_format):
            return 'converted!'
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': True})()
        assistant = Assistant()
    class Issue:
        def get_field(self, key, default=None):
            if key == 'summary': return 'summary-value'
            if key == 'description': return 'desc'
            return default
        def get(self, key): return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    draft = Draft(Mantis(), Issue())
    assert 'converted!' in draft.raw_draft

def test_materialize_skips_if_exists(tmp_path, monkeypatch):
    from src.drafts.draft import Draft
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = None
    class Issue:
        def get_field(self, key, default=None):
            return 'summary-value' if key == 'summary' else default
        def get(self, key): return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    # Create file first
    path = tmp_path / 'KEY-1.md'
    path.write_text('already here')
    draft = Draft(Mantis(), Issue())
    assert path.read_text() == 'already here'

def test_key_too_long(tmp_path):
    from src.drafts.draft import Draft
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = None
    class Issue:
        def get_field(self, key, default=None):
            return 'summary-value' if key == 'summary' else default
        def get(self, key): return 'K'*25
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    with pytest.raises(AssertionError, match='suspiciously long'):
        Draft(Mantis(), Issue()).key

def test_formatted_header_and_required_frontmatter(tmp_path):
    from src.drafts.draft import Draft
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = None
    class Issue:
        def get_field(self, key, default=None):
            return 'summary-value' if key == 'summary' else default
        def get(self, key): return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    draft = Draft(Mantis(), Issue())
    assert draft.formatted_header.startswith('[KEY-1]')
    assert 'header' in draft._required_frontmatter

def test_remove_draft_header():
    from src.drafts.draft import Draft
    class Dummy(Draft):
        def __init__(self): pass
        @property
        def summary(self): return 'Summary'
        def load_frontmatter(self):
            class F:
                content = '# Summary\n\nBody text'
            return F()
    draft = Dummy()
    assert draft._remove_draft_header() == 'Body text'

def test_raw_draft_empty_file(tmp_path):
    from src.drafts.draft import Draft
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = None
    class Issue:
        def get_field(self, key, default=None):
            return 'summary-value' if key == 'summary' else default
        def get(self, key): return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    draft = Draft(Mantis(), Issue())
    # Overwrite file with empty content
    draft.draft_path.write_text('')
    with pytest.raises(ValueError, match='does not contain any content'):
        _ = draft.raw_draft

def test_header_from_raw_index_error(tmp_path):
    from src.drafts.draft import Draft
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = None
    class Issue:
        def get_field(self, key, default=None):
            return 'summary-value' if key == 'summary' else default
        def get(self, key): return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---'
    draft = Draft(Mantis(), Issue())
    draft.draft_path.write_text('---\nmeta\n---\n')
    with pytest.raises(ValueError, match='Expected draft to start with a markdown header.*Got: ""'):
        _ = draft.header_from_raw

def test_header_from_raw_empty_index_error(tmp_path):
    from src.drafts.draft import Draft
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = None
    class Issue:
        def get_field(self, key, default=None):
            return 'summary-value' if key == 'summary' else default
        def get(self, key): return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n'
    draft = Draft(Mantis(), Issue())
    draft.draft_path.write_text('---\nmeta\n---\n\n')
    with pytest.raises(ValueError, match='Expected draft to start with a markdown header.*Got: ""'):
        _ = draft.header_from_raw

def test_content_setter_file_not_exists(tmp_path):
    from src.drafts.draft import Draft
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = None
    class Issue:
        def get_field(self, key, default=None):
            return 'summary-value' if key == 'summary' else default
        def get(self, key): return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    draft = Draft(Mantis(), Issue())
    # Remove the file
    draft.draft_path.unlink()
    with pytest.raises(FileNotFoundError):
        draft.content = 'new content'

def test_make_verbose_sets_content(tmp_path, monkeypatch):
    from src.drafts.draft import Draft
    class Assistant:
        def make_verbose(self, content):
            return content + ' verbose!'
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = Assistant()
    class Issue:
        def get_field(self, key, default=None):
            return 'summary-value' if key == 'summary' else default
        def get(self, key): return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    draft = Draft(Mantis(), Issue())
    result = draft.make_verbose()
    assert result['verbose_content'].endswith('verbose!')
