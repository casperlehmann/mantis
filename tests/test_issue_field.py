import pytest
from src.jira.issue_field import IssueField

class DummyFactory:
    def __init__(self, schema_type):
        self._schema_type = schema_type
    def field_by_key(self, key):
        return {'schema': {'type': self._schema_type}}

class DummyIssue:
    def __init__(self, field_value, editmeta_type, createmeta_type, non_editmeta_fields=None, non_createmeta_fields=None):
        self._field_value = field_value
        self.editmeta_factory = DummyFactory(editmeta_type)
        self.createmeta_factory = DummyFactory(createmeta_type)
        self.non_editmeta_fields = non_editmeta_fields or set()
        self.non_createmeta_fields = non_createmeta_fields or set()
        self.draft = {}
        self.editmeta_data = {'fields': {}}
        self.createmeta_data = {'fields': {}}
    def get_field(self, key):
        return self._field_value
    def update_field(self, data):
        self.updated_data = data
    def reload_issue(self):
        self.reloaded = True

# _extract_name_from_cached_object tests

def test_extract_none():
    issue = DummyIssue(None, 'string', 'string')
    field = IssueField(issue, 'summary')
    assert field._extract_name_from_cached_object() is None

def test_extract_project_status_issuetype():
    for key in ('project', 'status', 'issuetype'):
        issue = DummyIssue({'name': 'TestName'}, 'string', 'string')
        field = IssueField(issue, key)
        assert field._extract_name_from_cached_object() == 'TestName'

def test_extract_string():
    issue = DummyIssue('SomeString', 'string', 'string')
    field = IssueField(issue, 'summary')
    assert field._extract_name_from_cached_object() == 'SomeString'

def test_extract_user():
    issue = DummyIssue({'displayName': 'UserX'}, 'user', 'user')
    field = IssueField(issue, 'reporter')
    assert field._extract_name_from_cached_object() == 'UserX'

def test_extract_issuelink():
    issue = DummyIssue({'id': 123}, 'issuelink', 'issuelink')
    field = IssueField(issue, 'link')
    assert field._extract_name_from_cached_object() == 'issuelink'

def test_extract_both_na():
    issue = DummyIssue({'id': 123}, 'N/A', 'N/A')
    field = IssueField(issue, 'custom')
    with pytest.raises(ValueError):
        field._extract_name_from_cached_object()

def test_extract_one_na():
    issue = DummyIssue({'id': 123}, 'N/A', 'string')
    field = IssueField(issue, 'custom')
    with pytest.raises(NotImplementedError):
        field._extract_name_from_cached_object()

def test_extract_fallback_name():
    issue = DummyIssue({'name': 'Fallback'}, 'custom', 'custom')
    field = IssueField(issue, 'custom')
    assert field._extract_name_from_cached_object() == 'Fallback'
