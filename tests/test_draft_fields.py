import pytest
from src.drafts.draft import Draft
import src.drafts.template_md as template_md
from mantis.mantis_client import MantisClient

class MinimalJiraIssue:
    def __init__(self, content_dict=None):
        self._content = content_dict or {}
    def get_field(self, key, default=None):
        return self._content.get(key, default)
    def get(self, key):
        if key == 'key':
            return self._content.get('key', 'KEY-1')
        return self._content.get(key)


def make_draft(tmp_path, content_dict=None):
    class DummyOptions:
        drafts_dir = str(tmp_path)
        cache_dir = str(tmp_path / 'cache')
        plugins_dir = str(tmp_path / 'plugins')
        chat_gpt_activated = False
        chat_gpt_base_url = 'https://api.fakeai.com/v1'
        chat_gpt_api_key = 'dummy'
    options = DummyOptions()
    mantis = MantisClient(options)  # type: ignore
    # Ensure the content_dict has a 'key' for Draft
    if content_dict is not None and 'key' not in content_dict:
        content_dict = dict(content_dict)
        content_dict['key'] = 'KEY-1'
    issue = MinimalJiraIssue(content_dict)
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    return Draft(mantis, issue)  # type: ignore

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
