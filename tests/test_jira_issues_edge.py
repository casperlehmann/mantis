import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from jira.jira_issues import JiraIssue, JiraIssues
import tempfile

class DummyOptions:
    chat_gpt_activated = False
    chat_gpt_base_url = 'https://api.fakeai.com/v1'
    chat_gpt_api_key = 'dummy'
    drafts_dir = Path(tempfile.mkdtemp())
    cache_dir = Path(tempfile.mkdtemp()) / 'cache'
    plugins_dir = Path(tempfile.mkdtemp()) / 'plugins'

class DummyJira:
    def __init__(self, drafts_dir=None):
        self.mantis = Mock()
        self.mantis.drafts_dir = drafts_dir or Path(tempfile.mkdtemp())
        self.mantis.plugins_dir = Path(tempfile.mkdtemp()) / 'plugins'
        self.mantis.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.mantis.options = DummyOptions()
        self.system_config_loader = Mock()
        self.issues = Mock()
        self.project_id = '1'
        self.project_name = 'TEST'
    def update_field(self, key, data):
        self.updated = (key, data)
    def get_issue(self, key):
        return {'key': key, 'fields': {'summary': 's', 'issuetype': {'name': 'Bug'}, 'description': 'desc'}}
    def post_issue(self, data):
        return {'key': 'NEW-1'}
    def issuetype_name_to_id(self, name):
        return '10001'

class DummyDraft:
    def __init__(self):
        self._fields = {'summary': 'new summary', 'description': 'desc'}
    def iter_draft_field_items(self):
        return iter(self._fields.items())
    @property
    def content(self):
        return 'new description'
    def get(self, key, default=None):
        return self._fields.get(key, default)

def test_get_field_missing_and_none(tmp_path):
    issue = JiraIssue(DummyJira(tmp_path), {'key': 'K', 'fields': {'foo': None, 'summary': 's', 'description': 'desc'}})
    assert issue.get_field('foo', 'default') == 'default'
    assert issue.get_field('bar', 'default') == 'default'

def test_update_field_calls_jira(tmp_path):
    jira = DummyJira(tmp_path)
    issue = JiraIssue(jira, {'key': 'K', 'fields': {'summary': 's', 'description': 'desc'}})
    issue.update_field({'foo': 'bar'})
    assert jira.updated == ('K', {'foo': 'bar'})

def test_update_from_draft(tmp_path, monkeypatch):
    jira = DummyJira(tmp_path)
    # Patch get_editmeta_from_cache, get_editmeta, and system_config_loader.get_editmeta to return a valid dict with 'summary' and 'description' schema, 'key', and 'name'
    editmeta_dict = {
        'fields': {
            'summary': {
                'key': 'summary',
                'name': 'Summary',
                'required': True,
                'schema': {
                    'type': 'string',
                    'system': 'summary'
                }
            },
            'description': {
                'key': 'description',
                'name': 'Description',
                'required': True,
                'schema': {
                    'type': 'string',
                    'system': 'description'
                }
            }
        }
    }
    createmeta_dict = {
        'fields': [
            {
                'key': 'summary',
                'name': 'Summary',
                'required': True,
                'schema': {
                    'type': 'string',
                    'system': 'summary'
                }
            },
            {
                'key': 'description',
                'name': 'Description',
                'required': True,
                'schema': {
                    'type': 'string',
                    'system': 'description'
                }
            }
        ]
    }
    if not hasattr(jira.mantis, 'cache'):
        jira.mantis.cache = Mock()
    jira.mantis.cache.get_editmeta_from_cache = Mock(return_value=editmeta_dict)
    jira.mantis.cache.get_editmeta = Mock(return_value=editmeta_dict)
    jira.system_config_loader.get_editmeta = Mock(return_value=editmeta_dict)
    jira.system_config_loader.get_createmeta = Mock(return_value=createmeta_dict)
    issue = JiraIssue(jira, {'key': 'K', 'fields': {'summary': 's', 'description': 'desc', 'issuetype': {'name': 'Bug'}}})
    issue.draft = DummyDraft()
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    monkeypatch.setattr(issue, 'update_field', lambda data: setattr(issue, 'updated', data))
    monkeypatch.setattr(issue, 'reload_issue', lambda: setattr(issue, 'reloaded', True))
    issue.get_field = lambda key, default=None: 'desc'
    issue.update_from_draft()
    assert hasattr(issue, 'updated')
    assert hasattr(issue, 'reloaded')

def test_diff_issue_from_draft(tmp_path):
    jira = DummyJira(tmp_path)
    issue = JiraIssue(jira, {'key': 'K', 'fields': {'summary': 'old', 'description': 'desc'}})
    issue.draft = DummyDraft()
    with patch('jira.jira_issues.IssueField', autospec=True):
        issue.diff_issue_from_draft()

def test_reload_issue(tmp_path):
    jira = DummyJira(tmp_path)
    issue = JiraIssue(jira, {'key': 'K', 'fields': {'summary': 's', 'description': 'desc'}})
    # Ensure the mock returns a valid dict, not a Mock
    jira.issues.get = Mock(return_value={'key': 'K', 'fields': {'summary': 's', 'description': 'desc'}})
    issue.reload_issue()
    jira.issues.get.assert_called_with('K', force_skip_cache=True)

def test_create_missing_fields(tmp_path, monkeypatch):
    jira = DummyJira(tmp_path)
    issues = JiraIssues(jira)
    issues._allowed_types = ['Bug']
    jira.project_id = '1'
    jira.issuetype_name_to_id = lambda name: '10001'
    jira.post_issue = lambda data: {'key': 'NEW-1'}
    jira.get_issue = lambda key: {'key': key, 'fields': {'summary': 't', 'issuetype': {'name': 'Bug'}, 'description': 'desc'}}
    # Ensure the mock returns a valid dict, not a Mock
    cache_mock = Mock()
    cache_mock.get_issue = Mock(return_value=None)
    jira.mantis.cache = cache_mock
    jira.mantis._no_read_cache = True
    monkeypatch.setattr('builtins.print', lambda *a, **k: None)
    monkeypatch.setattr(JiraIssues, 'get', lambda self, key, force_skip_cache=False: JiraIssue(jira, {'key': key, 'fields': {'summary': 't', 'issuetype': {'name': 'Bug'}, 'description': 'desc'}}))
    data = {}
    resp = issues.create('Bug', 't', data)
    assert resp['key'] == 'NEW-1'
    assert data['issuetype']['id'] == '10001'
    assert data['summary'] == 't'
    assert data['project']['id'] == '1'
