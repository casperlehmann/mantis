import pytest

from mantis.drafts import Draft
from mantis.jira import JiraClient
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
            "description": "redacted",
            "project": "lolcorp",
            "reporter": "null",
        },
    }


def test_jira_draft(fake_jira: JiraClient, json_response):
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
        "header: '[TASK-1] Test issue'",
        "ignore: true",
        "parent: TASK-0",
        "summary: Test issue",
        "issuetype:",
        "issuetype: null",
        "project: lolcorp",
        "reporter: 'null'",
        "description: redacted",
        "assignee: Bobby Goodsky",
        "status: resolved",
        "---",
        "# Test issue",
        "",
        "redacted",
    )
    with open(fake_jira.drafts_dir / "TASK-1.md", "r") as f:
        for content in f.readlines():
            assert content.strip() in expectations, f"content.strip() ({content.strip()}) not in expectations in: {expectations}"
