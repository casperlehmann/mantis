import json
import os
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

    def get(self, file_name: str) -> str | None:
        if not (self.root / file_name).exists():
            return
        with open(self.root / file_name, "r") as f:
            return f.read()

    def get_decoded(self, file_name: str) -> dict:
        with open(self.root / file_name, "r") as f:
            return json.load(f)

    def get_issue(self, key: str):
        if self.client._no_cache:
            return
        issue_data = self.get(f"issues/{key}.json")
        if issue_data:
            return json.loads(issue_data)

    def write(self, file_name: str, contents: str):
        with open(self.root / file_name, "w") as f:
            return f.write(contents)

    def write_issue(self, key: str, data):
        self.write(f"issues/{key}.json", json.dumps(data))

    def remove(self, file_name: str):
        os.remove(self.root / file_name)

    def remove_issue(self, key: str):
        self.remove(f"issues/{key}.json")

    def iter_dir(self, identifier):
        if identifier == "issue_type_fields":
            for file in self.issue_type_fields.iterdir():
                yield file
