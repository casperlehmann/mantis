from mantis.drafts import Draft
import pytest
import os
import re
from mantis.jira import JiraClient, JiraAuth
import requests
from unittest.mock import patch

@pytest.fixture
def fake_jira_issues():
    pass

@pytest.fixture
def fake_jira(opts_from_fake_cli, mock_get_request):
    expected = {'key': 'TASK-1',
                'fields': {
                    'status': {'name': 'resolved'},
                    'summary': 'Test issue',
                    'parent': 'TASK-0',
                    # 'project': {'key': 'ABC-123'},
                    'issuetype': {'key': 'Task'},
                    'assignee': {'displayName': 'Bobby Goodsky'},
                }}
    mock_get_request.return_value.json.return_value = expected
    auth = JiraAuth(opts_from_fake_cli)
    return JiraClient(opts_from_fake_cli, auth)

from pathlib import Path
def test_JiraDraft(tmp_path, fake_jira: JiraClient):
    drafts_dir = tmp_path / 'drafts'
    drafts_dir.mkdir()
    fake_jira._no_cache = True
    task_1 = fake_jira.issues.get('TASK-44')
    assert type(task_1) == dict
    # assert task_1.get('fields', {}).get('project', {}) == {'key': 'ABC-123'}
    # assert task_1.get('fields', {}).get('project', {}).get('key') == 'ABC-123'
    assert len(list(drafts_dir.iterdir())) == 0
    draft = Draft(task_1, drafts_dir)
    assert len([*drafts_dir.iterdir()]) == 1
    # draft._materialize()
    # assert len(list(drafts_dir.iterdir())) == 1

    with open(drafts_dir / 'TASK-1.md', 'r') as f:
        content = f.read()
    # assert content == '1'
    assert 'assignee: Bobby Goodsky' in content

    expectations = (
                '---',
                'header: [TASK-1] Test issue',
                'ignore: True',
                'parent: TASK-0',
                'summary: Test issue',
                'issuetype: None',
                'assignee: Bobby Goodsky',
                '---',
                '# Test issue',
                '',
                'None',
    )
    with open(drafts_dir / 'TASK-1.md', 'r') as f:
        for content, expected in zip(f.readlines(), expectations):
            assert content.strip() == expected


