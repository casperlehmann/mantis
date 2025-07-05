import pytest
from src.drafts.draft import Draft
import src.drafts.template_md as template_md

class DummyMantis:
    options = type('opt', (), {'chat_gpt_activated': False})()
    assistant = None

def make_draft(tmp_path, content_dict=None):
    class Issue:
        def get_field(self, key, default=None):
            return content_dict.get(key, default) if content_dict else default
        def get(self, key):
            return 'KEY-1'
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    mantis = DummyMantis()
    mantis.drafts_dir = tmp_path
    return Draft(mantis, Issue())

def test_iter_draft_field_items_and_keys(tmp_path):
    # Write a draft file with extra fields
    draft = make_draft(tmp_path, {'summary': 'summary-value', 'extra': 'foo'})
    path = draft.draft_path
    path.write_text('---\nheader: h\nproject: p\nparent: pa\nsummary: s\nextra: foo\n---\n# summary-value\nBody')
    items = list(draft.iter_draft_field_items())
    keys = list(draft.iter_draft_field_keys())
    assert any(k == 'extra' and v == 'foo' for k, v in items)
    assert 'extra' in keys

def test_get_method(tmp_path):
    draft = make_draft(tmp_path, {'summary': 'summary-value', 'foo': 'bar'})
    path = draft.draft_path
    path.write_text('---\nheader: h\nproject: p\nparent: pa\nsummary: s\nfoo: bar\n---\n# summary-value\nBody')
    assert draft.get('foo') == 'bar'
    assert draft.get('nonexistent', 'default') == 'default'

def test_header_from_raw_empty_content(tmp_path):
    draft = make_draft(tmp_path, {'summary': 'summary-value'})
    path = draft.draft_path
    path.write_text('---\nmeta\n---')
    with pytest.raises(ValueError, match='Expected draft to start with a markdown header.*Got: ""'):
        _ = draft.header_from_raw

def test_header_from_raw_empty_line(tmp_path):
    draft = make_draft(tmp_path, {'summary': 'summary-value'})
    path = draft.draft_path
    path.write_text('---\nmeta\n---\n')
    with pytest.raises(ValueError, match='Expected draft to start with a markdown header.*Got: ""'):
        _ = draft.header_from_raw
