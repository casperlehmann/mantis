import pytest
import os
from mantis.jira import JiraClient, JiraAuth
import requests
from unittest.mock import patch

@pytest.fixture
def fake_jira(opts_from_fake_cli, mock_get_request):
    expected = {'key': 'TASK-1', 'fields': {'status': {'name': 'resolved'}}}
    mock_get_request.return_value.json.return_value = expected
    auth = JiraAuth(opts_from_fake_cli)
    return JiraClient(opts_from_fake_cli, auth)

def test_JiraIssuesGetFake(fake_jira):
    task_1 = fake_jira.issues.get('TASK-1')
    assert task_1.get('key') == 'TASK-1'
    assert task_1.get('fields') == {'status': {'name': 'resolved'}}

def test_JiraIssuesGetNonExistent(jira_client_from_fake_cli):
    jira_client_from_fake_cli._no_cache = True
    _mock_response = requests.models.Response()
    _mock_response.status_code = 404
    _mock_response.reason = "Not Found"
    with patch("requests.get", return_value=_mock_response):
        with pytest.raises(ValueError, match=('The issue "TEST-999" does not '
                           'exists in the project "TEST"')):
            jira_client_from_fake_cli.issues.get('TEST-999')
        with pytest.raises(ValueError, match="The requested issue does not exists."):
            jira_client_from_fake_cli.issues.get('NONEXISTENT-1')
        with pytest.raises(NotImplementedError, match=('Partial keys are not supported. '
                           'Please provide the full key for your issue: "PROJ-11"')):
            jira_client_from_fake_cli.issues.get('11')

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

