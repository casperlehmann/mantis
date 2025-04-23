from pathlib import Path
from typing import TYPE_CHECKING

# To-do: Create converter for Jira syntax to markdown.
j2m = lambda x: x

if TYPE_CHECKING:
    from mantis.jira import JiraIssue


class Draft:
    def __init__(self, issue: "JiraIssue", drafts_dir: Path = None) -> None:
        if not drafts_dir:
            drafts_dir = Path("drafts")
        self.dir = drafts_dir
        self.dir.mkdir(exist_ok=True)
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
        parent = self.issue.get("fields", {}).get("parent")
        summary = self.issue.get("fields", {}).get("summary")
        issuetype = self.issue.get("fields", {}).get("issuetype", {}).get("name")
        assignee = self.issue.get("fields", {}).get("assignee", {}).get("displayName")
        description = self.issue.get("fields", {}).get("description")

        with open(self.dir / (key + ".md"), "w") as f:
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
