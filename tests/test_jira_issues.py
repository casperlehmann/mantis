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

