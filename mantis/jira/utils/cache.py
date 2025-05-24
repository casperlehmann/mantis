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
        self.createmeta.mkdir(exist_ok=True)

    def invalidate(self) -> None:
        if self.root.exists():
            # This violently removes everything. Don't store anything important in the cache.
            shutil.rmtree(self.root)
        self.root.mkdir(exist_ok=True)
        self.issues.mkdir(exist_ok=True)
        self.system.mkdir(exist_ok=True)
        self.createmeta.mkdir(exist_ok=True)

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
    def createmeta(self) -> Path:
        return self.system / "createmeta"

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
        projects = self.get_from_system_cache(f"projects.json")
        if not projects:
            return None
        assert isinstance(projects, list), f'{projects} should be of type list. Got: {type(projects)}: {projects}'
        return projects

    def get_issuetypes_from_system_cache(self) -> dict[str, Any] | None:
        if self.client._no_read_cache:
            raise LookupError('Attempted to access cache when _no_read_cache is set')
        issuetypes = self.get_from_system_cache("issuetypes.json")
        if not issuetypes:
            return None
        assert isinstance(issuetypes, dict), f'{issuetypes} should be of type dict. Got: {type(issuetypes)}: {issuetypes}'
        return issuetypes

    def get_from_createmeta_cache(self, filename: str) -> dict[str, Any] | None:
        contents = self._get(self.createmeta, filename)
        if not contents:
            return None
        assert isinstance(contents, dict), f'Got: {type(contents)}: {contents}'
        return contents

    def get_createmeta_from_createmeta_cache(self, issuetype_name: str) -> dict[str, Any] | None:
        filename = f"createmeta_{issuetype_name.lower()}.json"
        return self.get_from_createmeta_cache(filename)

    def get_editmeta_from_createmeta_cache(self, issuetype_name: str) -> dict[str, Any] | None:
        filename = f"editmeta_{issuetype_name.lower()}.json"
        return self.get_from_createmeta_cache(filename)

    def _write(self, path: Path, filename: str, contents: str) -> int:
        with open(path / filename, "w") as f:
            return f.write(contents)

    def write_issue(self, key: str, data: dict) -> int:
        return self._write(self.issues, f"{key}.json", json.dumps(data))

    def write_to_system_cache(self, filename: str, issue_enums: str) -> None:
        self._write(self.system, filename, issue_enums)

    def write_issuetypes_to_system_cache(self, issuetypes: dict[str, Any]) -> None:
        self.write_to_system_cache("issuetypes.json", json.dumps(issuetypes))

    def write_to_createmeta(self, filename: str, createmeta: list[dict[str, Any]]) -> None:
        self._write(self.createmeta, filename, json.dumps(createmeta))

    def write_createmeta(self, issuetype_name: str, createmeta: list[dict[str, Any]]) -> None:
        self.write_to_createmeta(f"createmeta_{issuetype_name.lower()}.json", createmeta)

    def remove(self, filename: str) -> bool:
        if not (self.root / filename).exists():
            return False
        os.remove(self.root / filename)
        return True

    def remove_issue(self, key: str) -> bool:
        return self.remove(f"issues/{key}.json")

    def iter_dir(self, identifier: str) -> Generator[Path, None, None]:
        if identifier == "createmeta":
            for file in self.createmeta.iterdir():
                yield file
        if identifier == "issues":
            for file in self.issues.iterdir():
                yield file
