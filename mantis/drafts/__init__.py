from typing import Callable, TYPE_CHECKING

# To-do: Create converter for Jira syntax to markdown.
j2m: Callable[[str], str] = lambda x: x

if TYPE_CHECKING:
    from mantis.jira import JiraIssue
    from mantis.jira.jira_client import JiraClient


class Draft:
    def __init__(self, jira: "JiraClient", issue: "JiraIssue") -> None:
        assert jira.drafts_dir
        self.jira = jira
        self.issue = issue
        self._materialize()

    def _materialize(self):
        key = self.issue.get("key")
        # key = json_payload.get('key')
        assert key, "No key in issue"
        assert (
            len(key) < 20
        ), f'The length of the key is suspeciously long: "{key[:20]}..."'
        # project = self.issue.get('fields', {}).get('project', {}).get('key')
        parent = self.issue.get_field("parent", "None")
        summary = self.issue.get_field("summary")
        issuetype = self.issue.get_field("issuetype").get("name")
        assignee = self.issue.get_field("assignee", {})
        assignee = assignee.get("displayName")
        description = self.issue.get_field("description")

        with open(self.jira.drafts_dir / f"{key}.md", "w") as f:
            f.write(f"---\n")
            f.write(f"header: [{key}] {summary}\n")
            f.write(f"ignore: True\n")
            # f.write(f'project: {project}\n')
            f.write(f"parent: {parent}\n")
            f.write(f"summary: {summary}\n")
            f.write(f"issuetype: {issuetype}\n")
            f.write(f"assignee: {assignee}\n")
            f.write(f"---\n")
            f.write(f"# {summary}\n")
            f.write(f"\n")
            f.write(f"{j2m(description)}\n")
            f.write(f"\n")
            # f.write(f'\n')
            # f.write(f'{description}\n')
