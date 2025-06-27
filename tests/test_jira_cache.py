import json
import pytest

from mantis.jira import JiraClient
from tests.data import CacheData, get_issuetypes_response


class TestCache:
    @pytest.fixture(autouse=True)
    def _request_jira(self, fake_jira: JiraClient):
        self.jira = fake_jira

    @pytest.fixture(autouse=True)
    def _request_minimal_issue_payload(self, minimal_issue_payload: dict):
        self.issue_payload = minimal_issue_payload

    def test_cache_get_caches_jira_issue(self):
        assert not self.jira.mantis._no_read_cache
        assert self.jira.mantis.cache._get(self.jira.mantis.cache.issues, "TASK-1.json") is None

        with open(self.jira.mantis.cache.root / "issues/TASK-1.json", "w") as f:
            json.dump(self.issue_payload, f)

        decoded = self.jira.mantis.cache._get(self.jira.mantis.cache.issues, "TASK-1.json")
        assert decoded
        assert decoded.get("key", '') == "TASK-1"

    def test_cache_get_issue_returns_none_when_no_read_cache_is_set(self):
        # Make sure nothing is cached
        assert not self.jira.mantis._no_read_cache
        assert self.jira.mantis.cache.get_issue("TASK-1") is None

        # cache something
        with open(self.jira.mantis.cache.root / "issues/TASK-1.json", "w") as f:
            json.dump(self.issue_payload, f)
        something = self.jira.mantis.cache.get_issue("TASK-1")
        assert something is not None

        # Deactivate the cache and make sure nothing is retrieved
        self.jira.mantis._no_read_cache = True
        with pytest.raises(LookupError):
            nothing_2 = self.jira.mantis.cache.get_issue("TASK-1")
            assert nothing_2 is None

    def test_cache_remove_does_removals(self):
        # cache something
        with open(self.jira.mantis.cache.root / "issues/TASK-1.json", "w") as f:
            json.dump(self.issue_payload, f)
        something_1 = self.jira.mantis.cache.get_issue("TASK-1")
        assert something_1 is not None

        # remove with cache.remove
        assert self.jira.mantis.cache.remove("issues/TASK-1.json")
        assert not self.jira.mantis.cache.remove("issues/TASK-1.json")
        nothing_1 = self.jira.mantis.cache.get_issue("TASK-1")
        assert nothing_1 is None

    def test_cache_remove_issue_does_removals(self):
        # cache something
        with open(self.jira.mantis.cache.root / "issues/TASK-1.json", "w") as f:
            json.dump(self.issue_payload, f)
        something_2 = self.jira.mantis.cache.get_issue("TASK-1")
        assert something_2 is not None

        # remove with cache.remove_issue
        self.jira.mantis.cache.remove_issue("TASK-1")
        nothing_2 = self.jira.mantis.cache.get_issue("TASK-1")
        assert nothing_2 is None

    @pytest.mark.parametrize("identifier", [("createmeta")])
    def test_cache_iter_dir_yields_files(self, identifier: str):
        assert len(list(self.jira.mantis.cache.iter_dir(identifier))) == 0
        # cache something
        with open(self.jira.mantis.cache.system / f"{identifier}/some_file.json", "w") as f:
            f.write("{}")
        assert len(list(self.jira.mantis.cache.iter_dir(identifier))) == 1

    def test_cache_get_issuetypes_from_system_cache(self, requests_mock):
        requests_mock.get(f'{self.jira.mantis.http.api_url}/issue/createmeta/TEST/issuetypes', json=get_issuetypes_response)

        with open(self.jira.mantis.cache.system / "issuetypes.json", "w") as f:
            json.dump(CacheData().issuetypes, f)
        retrieved = self.jira.mantis.cache.get_issuetypes_from_system_cache()
        assert retrieved
        assert len(retrieved['issueTypes']) == 5
        subtask = [_type for _type in retrieved['issueTypes'] if _type['name'] == 'Subtask'][0]
        assert subtask["description"] == "Subtasks track small pieces of work that are part of a larger task.", (
                f'retrieved: {retrieved}')

    def test_persisted_issuetypes_data(self):
        selector = lambda field_name: {_[field_name] for _ in CacheData().issuetypes.get("issueTypes", {field_name: ''})}
        assert len(CacheData().issuetypes.get("issueTypes", [])) == 5
        assert selector('name') == {'Subtask', 'Story', 'Bug', 'Task', 'Epic'}
