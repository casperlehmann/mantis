from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantis.jira.jira_client import JiraClient


class Cache:
    def __init__(self, jira_client: "JiraClient") -> None:
        self.client = jira_client

        self.root = Path(self.client.options.cache_dir)
        self.root.mkdir(exist_ok=True)

        self.cache_issues = self.root / "issues"
        self.cache_issues.mkdir(exist_ok=True)
        self.cache_system = self.root / "system"
        self.cache_system.mkdir(exist_ok=True)
        self.cache_issue_type_fields = self.cache_system / "issue_type_fields"
        self.cache_issue_type_fields.mkdir(exist_ok=True)
