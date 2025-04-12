import pytest
import inspect

from jira import JiraOptions, JiraAuth, JiraClient, parse_args
from jira import fetch_enums

from .conftest import RequestsMock, RequestsResultMock

VAL = [
    {
        'description': 'Created by Jira Agile - do not edit or delete. Issue type for a user story.',
        'id': 6,
        'untranslatedName': 'Story'
    },
    {
        'description': "A small piece of work that's part of a larger task.",
        'id': 18,
        'untranslatedName': 'Sub-Task'
    },
    {
        'description': 'A collection of related bugs, stories, and tasks.',
        'id': 5,
        'untranslatedName': 'Epic'
    },
    {'description': 'A problem or error.', 'id': 1, 'untranslatedName': 'Bug'},
    {'description': 'A small, distinct piece of work.', 'id': 3, 'untranslatedName': 'Task'},
    {
        'description': 'A new feature of the product, which has yet to be developed.',
        'id': 17,
        'untranslatedName': 'New Feature'
    },
    {'description': 'Service Impacting Event', 'id': 10, 'untranslatedName': 'Incident'}
]

@pytest.fixture
def fake_jira_client_for_issue_type(opts_from_fake_cli):
    request_mock = RequestsMock(get_return = VAL)
    auth = JiraAuth(opts_from_fake_cli)
    return JiraClient(opts_from_fake_cli, auth, request_mock)

def test_fetch_issuetype_enums_mock(fake_jira_client_for_issue_type):
    types_filter = lambda d: int(d['id']) < 100 and d['name'] in ('Bug', 'Task', 'Epic', 'Story', 'Incident', 'New Feature', 'Sub-Task')
    mapping = {'id': 'id', 'description': 'description', 'untranslatedName': 'name'}
    caster_functions = {'id': int}
    issue_enums = fetch_enums(fake_jira_client_for_issue_type, endpoint = 'issuetype', filter = types_filter, mapping = mapping, caster_functions = caster_functions)
    assert len(issue_enums) == 7, f'Exactly seven matches the filter: {str(inspect.getsource(types_filter)).strip()}'
    issue_type_1_bugs = [_ for _ in issue_enums if _['id'] == 1]
    assert len(issue_type_1_bugs) == 1, f'Exactly one with id == 1'
    issue_type_1_bug = issue_type_1_bugs[0]
    assert issue_type_1_bug['name'] == 'Bug', 'Issue of id == 1 has wrong name'
    assert issue_type_1_bug['description'] == 'A problem or error.', 'Issue of id == 1 has wrong description'

def test_fetch_issuetype_enums_real(jira_client_from_user_toml):
    types_filter = lambda d: int(d['id']) < 100 and d['name'] in ('Bug', 'Task', 'Epic', 'Story', 'Incident', 'New Feature', 'Sub-Task')
    mapping = {'id': 'id', 'description': 'description', 'untranslatedName': 'name'}
    caster_functions = {'id': int}
    issue_enums = fetch_enums(jira_client_from_user_toml, endpoint = 'issuetype', filter = types_filter, mapping = mapping, caster_functions = caster_functions)
    assert len(issue_enums) == 7, f'Exactly seven matches the filter: {str(inspect.getsource(types_filter)).strip()}'
    issue_type_1_bugs = [_ for _ in issue_enums if _['id'] == 1]
    assert len(issue_type_1_bugs) == 1, f'Exactly one with id == 1'
    issue_type_1_bug = issue_type_1_bugs[0]
    assert issue_type_1_bug['name'] == 'Bug', 'Issue of id == 1 has wrong name'
    assert issue_type_1_bug['description'] == 'A problem or error.', 'Issue of id == 1 has wrong description'

