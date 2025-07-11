
from jira.jira_issues import JiraIssue
from mantis.mantis_client import MantisClient
from tests.data import CacheData


class TestJiraDraft:
    def test_jira_draft(self, fake_mantis: MantisClient, minimal_issue_payload, requests_mock):
        ecs_1 = CacheData().ecs_1
        ecs_1['fields']['assignee'] = {"displayName": "Bobby Goodsky"}
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/ECS-1', json=ecs_1)
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/ECS-2', json=CacheData().ecs_2)

        minimal_issue_payload['fields']['assignee'] = {"displayName": "Bobby Goodsky"}
        assert str(fake_mantis.cache.root) != ".jira_cache_test"
        assert str(fake_mantis.drafts_dir) != "drafts_test"
        
        assert len(list(fake_mantis.drafts_dir.iterdir())) == 0
        task_1 = fake_mantis.jira.issues.get("ECS-1")
        assert len([*fake_mantis.drafts_dir.iterdir()]) == 1
        assert isinstance(task_1, JiraIssue)

        minimal_issue_payload['key'] = "ECS-2"
        _ = fake_mantis.jira.issues.get("ECS-2")
        assert len([*fake_mantis.drafts_dir.iterdir()]) == 2

        with open(fake_mantis.drafts_dir / "ECS-1.md", "r") as f:
            content = f.read()
        assert "assignee: Bobby Goodsky" in content
        assert "Bobby Goodsky" == fake_mantis.jira.issues.get('ECS-1').draft.issue.get_field("assignee", {}).get(
            "displayName", ""
        )
        expectations = (
            "---",
            "header: '[ECS-1] (Sample) User Authentication'",
            "parent: null",
            "summary: (Sample) User Authentication",
            "issuetype:",
            "issuetype: Epic",
            "project: E-Commerce Checkout System",
            "reporter: Casper Lehmann",
            "description: redacted",
            "assignee: Bobby Goodsky",
            "status: In Progress",
            "---",
            "# (Sample) User Authentication",
            "",
            "Implement user authentication for the checkout system.",
        )
        with open(fake_mantis.drafts_dir / "ECS-1.md", "r") as f:
            for content in f.readlines():
                assert content.strip() in expectations, f"content.strip() ({[content.strip()]}) not in expectations in:\n\t{expectations}"

    def test_read_draft(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/ECS-1', json=CacheData().ecs_1)

        issue_key = 'ECS-1'
        issue = fake_mantis.jira.issues.get(key=issue_key)
        draft_data = issue.draft.read_draft()
        assert draft_data
        assert draft_data.content == "Implement user authentication for the checkout system."
        assert set(draft_data.keys()) == {
            'assignee',
            'header',
            'issuetype',
            'parent',
            'project',
            'reporter',
            'status',
            'summary',
        }
        issue_field = issue.get_field('summary', 'N/A')
        extracted_from_issue_field = issue_field if isinstance(issue_field, str) else issue_field.get('displayName') or issue_field.get('name')
        draft_field = draft_data.get('summary', 'N/A')
        assert extracted_from_issue_field == draft_field

    def test_read_content(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/ECS-1', json=CacheData().ecs_1)

        issue_key = 'ECS-1'
        issue = fake_mantis.jira.issues.get(key=issue_key)
        draft_content = issue.draft.content
        assert isinstance(draft_content, str)
        assert draft_content == "Implement user authentication for the checkout system."


def test_remove_draft_header(fake_mantis, requests_mock, tmp_path):
    requests_mock.get(f'{fake_mantis.http.api_url}/issue/ECS-1', json=CacheData().ecs_1)
    issue = fake_mantis.jira.issues.get(key="ECS-1")
    draft = issue.draft
    header = f"# {draft.summary}"
    body = "Some content\nMore content"
    # Write a draft file with the header
    draft_path = draft.draft_path
    with open(draft_path, "w") as f:
        f.write(f"{header}\n{body}")
    # Should remove the header
    result = draft._remove_draft_header()
    assert result == body
    # Write a draft file with a non-matching header
    with open(draft_path, "w") as f:
        f.write(f"# Not a header\n{body}")
    # Should not remove the header
    result2 = draft._remove_draft_header()
    assert result2 == f"# Not a header\n{body}"
