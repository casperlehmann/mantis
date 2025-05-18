import pytest

from mantis.drafts import Draft
from mantis.jira import JiraClient
from mantis.jira.jira_issues import JiraIssue


def test_jira_draft(fake_jira: JiraClient, minimal_issue_payload):
    minimal_issue_payload['fields']['assignee'] = {"displayName": "Bobby Goodsky"}
    assert str(fake_jira.cache.root) != ".jira_cache_test"
    assert str(fake_jira.drafts_dir) != "drafts_test"
    # assert str(fake_jira.cache.root) != str(fake_jira.drafts_dir)
    
    assert len(list(fake_jira.drafts_dir.iterdir())) == 0
    task_1 = fake_jira.issues.get("TASK-1")
    assert len([*fake_jira.drafts_dir.iterdir()]) == 1
    assert isinstance(task_1, JiraIssue)

    minimal_issue_payload['key'] = "TASK-2"
    task_2 = fake_jira.issues.get("TASK-2")
    assert len([*fake_jira.drafts_dir.iterdir()]) == 2

    with open(fake_jira.drafts_dir / "TASK-1.md", "r") as f:
        content = f.read()
    assert "assignee: Bobby Goodsky" in content
    assert "Bobby Goodsky" == fake_jira.issues.get('Task-1').draft.issue.get_field("assignee", {}).get(
        "displayName", ""
    )
    expectations = (
        "---",
        "header: '[TASK-1] redacted'",
        "ignore: true",
        "parent: redacted",
        "summary: redacted",
        "issuetype:",
        "issuetype: Task",
        "project: redacted",
        "reporter: redacted",
        "description: redacted",
        "assignee: Bobby Goodsky",
        "status: resolved",
        "---",
        "# redacted",
        "",
        "redacted",
    )
    with open(fake_jira.drafts_dir / "TASK-1.md", "r") as f:
        for content in f.readlines():
            assert content.strip() in expectations, f"content.strip() ({content.strip()}) not in expectations in: {expectations}"
