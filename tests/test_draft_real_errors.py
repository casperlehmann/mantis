import pytest
from src.drafts.draft import Draft

def test_remove_draft_header():
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
    draft.draft_path.write_text('')
    with pytest.raises(ValueError, match='does not contain any content'):
        _ = draft.raw_draft

def test_content_setter_file_not_exists(tmp_path):
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
    draft.draft_path.unlink()
    with pytest.raises(FileNotFoundError):
        draft.content = 'new content'
