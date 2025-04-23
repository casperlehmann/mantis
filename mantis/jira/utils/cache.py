from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantis.jira.jira_client import JiraClient


class Cache:
    def __init__(self, jira_client: "JiraClient") -> None:
        self.client = jira_client

        self.cache_dir = Path(self.client.options.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        (self.cache_dir / "issues").mkdir(exist_ok=True)
        (self.cache_dir / "system").mkdir(exist_ok=True)
        (self.cache_dir / "system" / "issue_type_fields").mkdir(exist_ok=True)

