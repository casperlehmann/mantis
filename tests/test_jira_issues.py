import pytest
import os
from jira import JiraIssues, JiraClient, JiraAuth
import requests

@pytest.fixture
def fake_jira(opts_from_fake_cli, mock_get_request):
    expected = {'key': 'TASK-1', 'fields': {'status': {'name': 'resolved'}}}
    mock_get_request.return_value.json.return_value = expected
    auth = JiraAuth(opts_from_fake_cli)
    return JiraClient(opts_from_fake_cli, auth, requests)

def test_JiraIssuesGetFake(fake_jira):
    task_1 = fake_jira.issues.get('TASK-1')
    assert task_1.get('key') == 'TASK-1'
    assert task_1.get('fields') == {'status': {'name': 'resolved'}}

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

