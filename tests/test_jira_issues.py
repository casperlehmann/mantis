import pytest
import os
import re
from mantis.jira import JiraClient, JiraAuth
import requests
from unittest.mock import patch, MagicMock

@pytest.fixture
def fake_jira(opts_from_fake_cli, mock_get_request):
    expected = {'key': 'TASK-1', 'fields': {'status': {'name': 'resolved'}}}
    # expected = {'key': 'TASK-1',
    #         'fields': {
    #             'status': {'name': 'resolved'},
    #             'project': {'key': 'ABC-123'},
    #             'issuetype': {'key': 'Task'},
    #             'assignee': {'displayName': 'Bobby Goodsky'},
    #         }}
    mock_get_request.return_value.json.return_value = expected
    auth = JiraAuth(opts_from_fake_cli)
    return JiraClient(opts_from_fake_cli, auth)

def test_JiraIssuesGetFake(fake_jira):
    task_1 = fake_jira.issues.get('TASK-1')
    assert task_1.get('key') == 'TASK-1'
    assert task_1.get('fields', {}).get('status') == {'name': 'resolved'}

def test_JiraIssuesGetFake2(jira_client_from_fake_cli_no_cache):
    expected = {'key': 'TASK-1', 'fields': {'status': {'name': 'resolved'}}}
    mock_response = MagicMock(spec=requests.models.Response)
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json = lambda: expected
    mock_response.headers = {"Content-Type": "text/plain"}
    mock_response.text = 'ULTI_JOKE'
    with patch("requests.get", return_value=mock_response):
        task_1 = jira_client_from_fake_cli_no_cache.issues.get('TASK-1')
    assert task_1.get('key') == 'TASK-1'
    assert task_1.get('fields', {}).get('status') == {'name': 'resolved'}

def test_JiraIssuesGetNonExistent(jira_client_from_fake_cli):
    jira_client_from_fake_cli._no_cache = True
    mock_response = requests.models.Response()
    # mock_response.ok = False
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    with patch("requests.get", return_value=mock_response):
        with pytest.raises(ValueError,
                           match=('The issue "TEST-999" does not exists in '
                           'the project "TEST"')):
            jira_client_from_fake_cli.issues.get('TEST-999')
        with pytest.raises(ValueError,
                           match='The requested issue does not exist. Note '
                           'that the provided key "NONEXISTENT-1" does not '
                           'appear to match your configured project "TEST"'):
            jira_client_from_fake_cli.issues.get('NONEXISTENT-1')
        with pytest.raises(NotImplementedError,
                           match=('Partial keys are not supported. Please '
                           'provide the full key for your issue: "PROJ-11"')):
            jira_client_from_fake_cli.issues.get('11')
        with pytest.raises(ValueError,
                           match=('Issue number "PROJ" in key "1-PROJ" must '
                           'be numeric')):
            jira_client_from_fake_cli.issues.get('1-PROJ')
        with pytest.raises(ValueError,
                           match=re.escape('Whitespace in key is not allowed '
                           '("PROJ-1 ")')):
            jira_client_from_fake_cli.issues.get('PROJ-1 ')

@pytest.mark.skipif(not os.path.exists("options.toml"), reason='File "options.toml" does not exist')
@pytest.mark.skipif(not os.getenv('EXECUTE_SKIPPED'), reason="This is a live test against the Jira api")
def test_JiraIssuesGetReal(jira_client_from_user_toml):
    test_3 = jira_client_from_user_toml.issues.get('TEST-3')
    assert test_3.get('key') == 'TEST-3'
    test_3_fields = test_3.get('fields', {})
    assert test_3_fields != {}
    test_3_status = test_3_fields.get('status', {})
    assert test_3_status != {}
    test_3_status_name = test_3_status.get('name', {})
    assert test_3_status_name == 'In Progress'

def test_JiraIssuesCreate(jira_issues_from_fake_cli, mock_post_request):
    with pytest.raises(ValueError):
        issue = jira_issues_from_fake_cli.create(issue_type='Bug', title='Tester', data={})
    expected = {'key': 'TASK-1', 'fields': {'status': {'name': 'In Progress'}, 'issuetype': {'name': 'Bug'}}}
    mock_post_request.return_value.json.return_value = expected
    issue = jira_issues_from_fake_cli.create(issue_type='Bug', title='Tester', data={'Summary':'a'})
    fields = issue.get('fields', {})
    assert fields != {}, "Object 'fields' is empty"
    issuetype = fields.get('issuetype', {})
    assert issuetype != {}, "Object 'issuetype' is empty"
    name = issuetype.get('name')
    assert name is not None, "Expected 'name' to be present in 'issuetype'"
    assert name == 'Bug', "Expected issue type name to be 'Bug'"

