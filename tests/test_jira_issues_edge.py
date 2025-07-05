import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from jira.jira_issues import JiraIssue, JiraIssues
import tempfile

class DummyJira:
    def __init__(self, drafts_dir=None):
        self.mantis = Mock()
        self.mantis.drafts_dir = drafts_dir or Path(tempfile.mkdtemp())
        self.system_config_loader = Mock()
        self.issues = Mock()
        self.project_id = '1'
        self.project_name = 'TEST'
    def update_field(self, key, data):
        self.updated = (key, data)
    def get_issue(self, key):
        return {'key': key, 'fields': {'summary': 's', 'issuetype': {'name': 'Bug'}}}
    def post_issue(self, data):
        return {'key': 'NEW-1'}
    def issuetype_name_to_id(self, name):
        return '10001'

class DummyDraft:
    def iter_draft_field_items(self):
        return iter([('summary', 'new summary'), ('description', 'desc')])
    @property
    def content(self):
        return 'new description'

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
    issue = JiraIssue(jira, {'key': 'K', 'fields': {'summary': 's', 'description': 'desc'}})
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
    jira.issues.get = Mock()
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
    jira.mantis.cache = Mock()
    jira.mantis._no_read_cache = True
    monkeypatch.setattr('builtins.print', lambda *a, **k: None)
    monkeypatch.setattr(JiraIssues, 'get', lambda self, key, force_skip_cache=False: JiraIssue(jira, {'key': key, 'fields': {'summary': 't', 'issuetype': {'name': 'Bug'}, 'description': 'desc'}}))
    data = {}
    resp = issues.create('Bug', 't', data)
    assert resp['key'] == 'NEW-1'
    assert data['issuetype']['id'] == '10001'
    assert data['summary'] == 't'
    assert data['project']['id'] == '1'
