from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantis.jira.jira_client import JiraClient


class Cache:
    def __init__(self, jira_client: "JiraClient") -> None:
        self.client = jira_client

        self.cache_dir = Path(self.client.options.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.cache_issues = self.cache_dir / "issues"
        self.cache_issues.mkdir(exist_ok=True)
        self.cache_system = self.cache_dir / "system"
        self.cache_system.mkdir(exist_ok=True)
        self.cache_issue_type_fields = self.cache_system / "issue_type_fields"
        self.cache_issue_type_fields.mkdir(exist_ok=True)
