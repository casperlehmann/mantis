import json
import pytest

from mantis.jira import JiraClient
from tests.data import CacheData, get_issuetypes_response


class TestCache:
    @pytest.fixture(autouse=True)
    def _request_minimal_issue_payload(self, minimal_issue_payload: dict):
        self.issue_payload = minimal_issue_payload

    def test_cache_get_caches_jira_issue(self, fake_jira: JiraClient):
        assert not fake_jira._no_read_cache
        assert fake_jira.cache._get(fake_jira.cache.issues, "TASK-1.json") is None

        with open(fake_jira.cache.root / "issues/TASK-1.json", "w") as f:
            json.dump(self.issue_payload, f)

        decoded = fake_jira.cache._get(fake_jira.cache.issues, "TASK-1.json")
        assert decoded
        assert decoded.get("key", '') == "TASK-1"

    def test_cache_get_issue_returns_none_when_no_read_cache_is_set(self, fake_jira: JiraClient):
        # Make sure nothing is cached
        assert not fake_jira._no_read_cache
        assert fake_jira.cache.get_issue("TASK-1") is None

        # cache something
        with open(fake_jira.cache.root / "issues/TASK-1.json", "w") as f:
            json.dump(self.issue_payload, f)
        something = fake_jira.cache.get_issue("TASK-1")
        assert something is not None

        # Deactivate the cache and make sure nothing is retrieved
        fake_jira._no_read_cache = True
        with pytest.raises(LookupError):
            nothing_2 = fake_jira.cache.get_issue("TASK-1")
            assert nothing_2 is None

    def test_cache_remove_does_removals(self, fake_jira: JiraClient):
        # cache something
        with open(fake_jira.cache.root / "issues/TASK-1.json", "w") as f:
            json.dump(self.issue_payload, f)
        something_1 = fake_jira.cache.get_issue("TASK-1")
        assert something_1 is not None

        # remove with cache.remove
        assert fake_jira.cache.remove("issues/TASK-1.json")
        assert not fake_jira.cache.remove("issues/TASK-1.json")
        nothing_1 = fake_jira.cache.get_issue("TASK-1")
        assert nothing_1 is None

    def test_cache_remove_issue_does_removals(self, fake_jira: JiraClient):
        # cache something
        with open(fake_jira.cache.root / "issues/TASK-1.json", "w") as f:
            json.dump(self.issue_payload, f)
        something_2 = fake_jira.cache.get_issue("TASK-1")
        assert something_2 is not None

        # remove with cache.remove_issue
        fake_jira.cache.remove_issue("TASK-1")
        nothing_2 = fake_jira.cache.get_issue("TASK-1")
        assert nothing_2 is None

    @pytest.mark.parametrize("identifier", [("createmeta")])
    def test_cache_iter_dir_yields_files(self, fake_jira: JiraClient, identifier: str):
        assert len(list(fake_jira.cache.iter_dir(identifier))) == 0
        # cache something
        with open(fake_jira.cache.system / f"{identifier}/some_file.json", "w") as f:
            f.write("{}")
        assert len(list(fake_jira.cache.iter_dir(identifier))) == 1

    def test_cache_get_issuetypes_from_system_cache(self, fake_jira: JiraClient, requests_mock):
        with open(fake_jira.cache.system / "issuetypes.json", "w") as f:
            json.dump(CacheData().issuetypes, f)
        retrieved = fake_jira.cache.get_issuetypes_from_system_cache()
        assert retrieved
        assert len(retrieved['issueTypes']) == 5
        subtask = [_type for _type in retrieved['issueTypes'] if _type['name'] == 'Subtask'][0]
        assert subtask["description"] == "Subtasks track small pieces of work that are part of a larger task.", (
                f'retrieved: {retrieved}')

    def test_persisted_issuetypes_data(self):
        selector = lambda field_name: {_[field_name] for _ in CacheData().issuetypes.get("issueTypes", {field_name: ''})}
        assert len(CacheData().issuetypes.get("issueTypes", [])) == 5
        assert selector('name') == {'Subtask', 'Story', 'Bug', 'Task', 'Epic'}
