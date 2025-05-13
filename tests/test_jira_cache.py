import pytest

from mantis.jira import JiraClient


def test_cache_get_caches_jira_issue(fake_jira: JiraClient):
    assert not fake_jira._no_read_cache
    assert fake_jira.cache._get(fake_jira.cache.issues, "TASK-1.json") is None

    with open(fake_jira.cache.root / "issues/TASK-1.json", "w") as f:
        f.write('{"fields": {"status": {"name": "resolved"}}, "key": "TASK-1"}')

    decoded = fake_jira.cache._get(fake_jira.cache.issues, "TASK-1.json")
    assert decoded == {"fields": {"status": {"name": "resolved"}}, "key": "TASK-1"}


def test_cache_get_issue_returns_none_when_no_read_cache_is_set(fake_jira: JiraClient):
    # Make sure nothing is cached
    assert not fake_jira._no_read_cache
    assert fake_jira.cache.get_issue("TASK-1") is None

    # cache something
    with open(fake_jira.cache.root / "issues/task-1.json", "w") as f:
        f.write('{"fields": {"status": {"name": "resolved"}}, "key": "task-1"}')
    something = fake_jira.cache.get_issue("task-1")
    assert something is not None

    # Deactivate the cache and make sure nothing is retrieved
    fake_jira._no_read_cache = True
    with pytest.raises(LookupError):
        nothing_2 = fake_jira.cache.get_issue("TASK-1")
        assert nothing_2 is None


def test_cache_remove_does_removals(fake_jira: JiraClient):
    # cache something
    with open(fake_jira.cache.root / "issues/task-1.json", "w") as f:
        f.write('{"fields": {"status": {"name": "resolved"}}, "key": "task-1"}')
    something_1 = fake_jira.cache.get_issue("task-1")
    assert something_1 is not None

    # remove with cache.remove
    assert fake_jira.cache.remove("issues/task-1.json")
    assert not fake_jira.cache.remove("issues/task-1.json")
    nothing_1 = fake_jira.cache.get_issue("task-1")
    assert nothing_1 is None


def test_cache_remove_issue_does_removals(fake_jira: JiraClient):
    # cache something
    with open(fake_jira.cache.root / "issues/task-1.json", "w") as f:
        f.write('{"fields": {"status": {"name": "resolved"}}, "key": "task-1"}')
    something_2 = fake_jira.cache.get_issue("task-1")
    assert something_2 is not None

    # remove with cache.remove_issue
    fake_jira.cache.remove_issue("task-1")
    nothing_2 = fake_jira.cache.get_issue("task-1")
    assert nothing_2 is None


@pytest.mark.parametrize(
    "identifier",
    [
        ("issuetype_fields"),
    ],
)
def test_cache_iter_dir_yields_files(fake_jira: JiraClient, identifier: str):
    assert len(list(fake_jira.cache.iter_dir(identifier))) == 0
    # cache something
    with open(fake_jira.cache.system / f"{identifier}/some_file.json", "w") as f:
        f.write("{}")
    assert len(list(fake_jira.cache.iter_dir(identifier))) == 1
