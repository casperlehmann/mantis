import json
import os
from pathlib import Path
import shutil
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from mantis.jira.jira_client import JiraClient


class CacheMissException(Exception):
    pass


class Cache:
    def __init__(self, jira_client: "JiraClient") -> None:
        self.client = jira_client
        self.root.mkdir(exist_ok=True)
        self.issues.mkdir(exist_ok=True)
        self.system.mkdir(exist_ok=True)
        self.issuetype_fields.mkdir(exist_ok=True)

    def invalidate(self):
        if self.root.exists:
            # This violently removes everything. Don't store anything important in the cache.
            shutil.rmtree(self.root)
        self.root.mkdir(exist_ok=True)
        self.issues.mkdir(exist_ok=True)
        self.system.mkdir(exist_ok=True)
        self.issuetype_fields.mkdir(exist_ok=True)

    @property
    def root(self) -> Path:
        return Path(self.client.options.cache_dir)

    @property
    def issues(self) -> Path:
        return self.root / "issues"

    @property
    def system(self) -> Path:
        return self.root / "system"

    @property
    def issuetype_fields(self) -> Path:
        return self.system / "issuetype_fields"

    def _get(self, path: Path, filename: str) -> dict | None:
        if self.client._no_read_cache:
            raise LookupError('Attempted to access cache when _no_read_cache is set')
        if not (path / filename).exists():
            return None
        with open(path / filename, "r") as f:
            return json.load(f)

    def get_issue(self, key: str) -> dict | None:
        if self.client._no_read_cache:
            raise LookupError('Attempted to access cache when _no_read_cache is set')
        return self._get(self.issues, f"{key}.json")
    
    def get_from_system_cache(self, filename: str) -> dict[str, Any] | list[dict[str, Any]] | None:
        if self.client._no_read_cache:
            raise LookupError('Attempted to access cache when _no_read_cache is set')
        return self._get(self.system, filename)

    def get_projects_from_system_cache(self) -> dict[str, Any] | list[dict[str, Any]] | None:
        if self.client._no_read_cache:
            raise LookupError('Attempted to access cache when _no_read_cache is set')
        return self.get_from_system_cache(f"projects.json")

    def get_issuetypes_from_system_cache(self) -> list[dict[str, Any]] | None:
        if self.client._no_read_cache:
            raise LookupError('Attempted to access cache when _no_read_cache is set')
        issuetypes = self.get_from_system_cache("issuetypes.json")
        if not issuetypes:
            return None
        assert isinstance(issuetypes, list), f'{issuetypes} should be of type list. Got: {type(issuetypes)}'
        return issuetypes

    def get_from_issuetype_fields_cache(self, filename: str) -> dict[str, Any] | None:
        contents = self._get(self.issuetype_fields, filename)
        if not contents:
            return None
        assert isinstance(contents, dict), f'Got: {type(contents)}: {contents}'
        return contents

    def get_createmeta_from_issuetype_fields_cache(self, issuetype_name: str) -> dict[str, Any] | None:
        filename = f"createmeta_{issuetype_name.lower()}.json"
        return self.get_from_issuetype_fields_cache(filename)

    def get_editmeta_from_issuetype_fields_cache(self, issuetype_name: str) -> dict[str, Any] | None:
        filename = f"editmeta_{issuetype_name.lower()}.json"
        return self.get_from_issuetype_fields_cache(filename)

    def _write(self, path: Path, filename: str, contents: str) -> int:
        with open(path / filename, "w") as f:
            return f.write(contents)

    def write_issue(self, key: str, data: dict) -> int:
        return self._write(self.issues, f"{key}.json", json.dumps(data))

    def write_to_system_cache(self, filename: str, issue_enums: str) -> None:
        self._write(self.system, filename, issue_enums)

    def write_issuetypes_to_system_cache(self, issuetypes: list[dict[str, Any]]) -> None:
        self.write_to_system_cache("issuetypes.json", json.dumps(issuetypes))

    def write_to_issuetype_fields(self, filename: str, issuetype_fields: list[dict[str, Any]]) -> None:
        self._write(self.issuetype_fields, filename, json.dumps(issuetype_fields))

    def write_createmeta(self, issuetype_name: str, issuetype_fields: list[dict[str, Any]]) -> None:
        self.write_to_issuetype_fields(f"createmeta_{issuetype_name.lower()}.json", issuetype_fields)

    def write_editemeta(self, issuetype_name: str, issuetype_fields: list[dict[str, Any]]) -> None:
        self.write_to_issuetype_fields(f"editmeta_{issuetype_name.lower()}.json", issuetype_fields)

    def remove(self, filename: str) -> bool:
        if not (self.root / filename).exists():
            return False
        os.remove(self.root / filename)
        return True

    def remove_issue(self, key: str) -> bool:
        return self.remove(f"issues/{key}.json")

    def iter_dir(self, identifier: str) -> Generator[Path, None, None]:
        if identifier == "issuetype_fields":
            for file in self.issuetype_fields.iterdir():
                yield file
