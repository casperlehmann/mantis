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
