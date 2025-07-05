import pytest
from src.drafts.draft import Draft

# --- Real Draft instantiation and file tests ---

def test_real_draft_import(tmp_path):
    class DummyMantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = None
    class DummyIssue:
        def get_field(self, key, default=None):
            return 'summary-value' if key == 'summary' else default
        def get(self, key):
            return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    draft = Draft(DummyMantis(), DummyIssue())
    assert draft.summary == 'summary-value'
    assert draft.key == 'KEY-1'
    assert draft.draft_path.exists()
    assert 'summary-value' in draft.raw_draft

def test_j2m_identity():
    from src.drafts.draft import j2m
    assert j2m("foo") == "foo"
