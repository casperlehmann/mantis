import pytest
from src.jira.issue_field import IssueField

class DummyFactory:
    def __init__(self, schema_type):
        self._schema_type = schema_type
    def field_by_key(self, key):
        return {'schema': {'type': self._schema_type}}

class DummyIssue:
    def __init__(self, field_value, editmeta_type, createmeta_type, draft_value=None, non_meta_fields=None, non_editmeta_fields=None, non_createmeta_fields=None):
        self._field_value = field_value
        self.editmeta_factory = DummyFactory(editmeta_type)
        self.createmeta_factory = DummyFactory(createmeta_type)
        self.non_editmeta_fields = non_editmeta_fields or set()
        self.non_createmeta_fields = non_createmeta_fields or set()
        self.non_meta_fields = non_meta_fields or set()
        self.draft = {} if draft_value is None else {"summary": draft_value}
        self.editmeta_data = {'fields': {"summary": {}}}
        self.createmeta_data = {'fields': {"summary": {}}}
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

# check_field tests

def test_check_field_both_na_in_non_meta_fields():
    issue = DummyIssue("irrelevant", 'N/A', 'N/A', draft_value=None, non_meta_fields={"summary"})
    field = IssueField(issue, 'summary')
    with pytest.raises(ValueError, match='cannot be set'):
        field.check_field()

def test_check_field_both_na_not_in_non_meta_fields():
    issue = DummyIssue("irrelevant", 'N/A', 'N/A', draft_value=None, non_meta_fields=set())
    field = IssueField(issue, 'summary')
    with pytest.raises(ValueError, match='neither createmeta nor editmeta schema'):
        field.check_field()

def test_check_field_types_not_equal():
    issue = DummyIssue("irrelevant", 'string', 'user', draft_value=None)
    field = IssueField(issue, 'summary')
    with pytest.raises(ValueError, match='not equal'):
        field.check_field()

def test_check_field_value_matches_draft(capsys):
    issue = DummyIssue("foo", 'string', 'string', draft_value="foo")
    field = IssueField(issue, 'summary')
    assert field.check_field() is True
    out = capsys.readouterr().out
    assert 'summary' in out and '(type: string):' in out

def test_check_field_value_differs_from_draft(capsys):
    issue = DummyIssue("foo", 'string', 'string', draft_value="bar")
    field = IssueField(issue, 'summary')
    assert field.check_field() is True
    out = capsys.readouterr().out
    assert 'foo -> bar' in out
