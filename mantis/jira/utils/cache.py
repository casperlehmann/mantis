from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantis.jira.jira_client import JiraClient


class Cache:
    def __init__(self, jira_client: "JiraClient") -> None:
        self.client = jira_client

        self.root = Path(self.client.options.cache_dir)
        self.root.mkdir(exist_ok=True)

        self.issues = self.root / "issues"
        self.issues.mkdir(exist_ok=True)
        self.system = self.root / "system"
        self.system.mkdir(exist_ok=True)
        self.issue_type_fields = self.system / "issue_type_fields"
        self.issue_type_fields.mkdir(exist_ok=True)

    def write(self, file_name: str, contents: str):
        with open(self.root / file_name, "w") as f:
            return f.write(contents)
