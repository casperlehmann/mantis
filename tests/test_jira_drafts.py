from pathlib import Path

import pytest

from mantis.drafts import Draft
from mantis.jira import JiraAuth, JiraClient
from mantis.jira.jira_issues import JiraIssue


@pytest.fixture
def json_response(mock_get_request):
    mock_get_request.return_value.json.return_value = {
        "key": "TASK-1",
        "fields": {
            "status": {"name": "resolved"},
            "summary": "Test issue",
            "parent": "TASK-0",
            "issuetype": {"key": "Task"},
            "assignee": {"displayName": "Bobby Goodsky"},
        },
    }


def test_jira_draft(fake_jira: JiraClient, json_response):
    fake_jira._no_read_cache = True
    assert str(fake_jira.cache.root) != ".jira_cache_test"
    assert str(fake_jira.drafts_dir) != "drafts_test"
    # assert str(fake_jira.cache.root) != str(fake_jira.drafts_dir)
    assert len(list(fake_jira.drafts_dir.iterdir())) == 0

    # assert list(fake_jira.drafts_dir.iterdir())[0] == ""
    task_1 = fake_jira.issues.get("TASK-44")
    assert type(task_1) == JiraIssue
    draft = Draft(fake_jira, task_1)
    assert len([*fake_jira.drafts_dir.iterdir()]) == 1

    with open(fake_jira.drafts_dir / "TASK-1.md", "r") as f:
        content = f.read()
    assert "assignee: Bobby Goodsky" in content
    assert "Bobby Goodsky" == draft.issue.get_field("assignee", {}).get(
        "displayName", ""
    )
    expectations = (
        "---",
        "header: [TASK-1] Test issue",
        "ignore: True",
        "parent: TASK-0",
        "summary: Test issue",
        "issuetype: None",
        "assignee: Bobby Goodsky",
        "---",
        "# Test issue",
        "",
        "None",
    )
    with open(fake_jira.drafts_dir / "TASK-1.md", "r") as f:
        for content, expected in zip(f.readlines(), expectations):
            assert content.strip() == expected
