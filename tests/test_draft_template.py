import pytest
from src.drafts.draft import Draft

# --- Template/Frontmatter/Body tests ---

def test_generate_frontmatter_true_false(tmp_path):
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
    assert draft.template.metadata['header'] == '[KEY-1] summary-value'

def test_generate_frontmatter_true_false_branch(tmp_path):
    from src.drafts.draft import Draft
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = None
    class Issue:
        def get_field(self, key, default=None):
            if key == 'header': return 'should-not-be-used'
            if key == 'summary': return 'summary-value'
            return default
        def get(self, key): return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: True\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    draft = Draft(Mantis(), Issue())
    assert draft.template.metadata['header'] == '[KEY-1] summary-value'

def test_generate_frontmatter_dict_branch(tmp_path):
    from src.drafts.draft import Draft
    class Mantis:
        drafts_dir = tmp_path
        options = type('opt', (), {'chat_gpt_activated': False})()
        assistant = None
    class Issue:
        def get_field(self, key, default=None):
            if key == 'assignee':
                return {'displayName': 'Display Name', 'name': 'User Name', 'key': 'UKEY'}
            if key == 'summary':
                return 'summary-value'
            return default
        def get(self, key): return 'KEY-1'
    import src.drafts.template_md as template_md
    template_md.template = '---\nheader: h\nproject: p\nparent: pa\nsummary: s\nstatus: st\nissuetype: it\nassignee: a\nreporter: r\n---\n{summary}\n{description}'
    draft = Draft(Mantis(), Issue())
    assert draft.template.metadata['assignee'] == 'Display Name'
