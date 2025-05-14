import json
from unittest.mock import patch

import pytest

from mantis.jira import JiraClient
from mantis.jira.utils.cache import CacheMissException
from mantis.jira.utils.jira_types import ProjectFieldKeys
from tests.data import get_issuetypes_response, update_projects_cache_response, CacheData
from tests.test_jira_types import ISSUETYPEFIELDS


@patch("mantis.jira.jira_client.requests.get")
def test_config_loader_update_issuetypes_writes_to_cache(
    mock_get, fake_jira: JiraClient
):
    mock_get.return_value.json.return_value = get_issuetypes_response
    config_loader = fake_jira.system_config_loader
    assert len(list(fake_jira.cache.system.iterdir())) == 1, (
        f"Not empty: {fake_jira.cache.system}")

    config_loader.update_issuetypes_cache()
    assert len(list(fake_jira.cache.system.iterdir())) == 2, (
        f"Not empty: {fake_jira.cache.system}")


def test_persisted_issuetypes_data():
    assert hasattr(CacheData, 'issuetypes')
    selector = lambda field_name: [_[field_name] for _ in CacheData.issuetypes]
    assert len(CacheData.issuetypes) == 5
    assert selector('name') == ['Subtask', 'Story', 'Bug', 'Task', 'Epic']
    assert CacheData.issuetypes[0].get('scope') == {"type": "PROJECT", "project": {"id": "10000"}}


@patch("mantis.jira.jira_client.requests.get")
def test_cache_get_issuetypes_from_system_cache(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = get_issuetypes_response
    cache = fake_jira.cache
    with open(fake_jira.cache.system / "issuetypes.json", "w") as f:
        json.dump(CacheData.issuetypes, f)
    retrieved = cache.get_issuetypes_from_system_cache()
    assert retrieved
    assert retrieved[0].get("description") == (
        "Subtasks track small pieces of work that are part of a larger task.")


@patch("mantis.jira.jira_client.requests.get")
def test_config_loader_loop_yields_files(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = get_issuetypes_response
    config_loader = fake_jira.system_config_loader
    assert len(list(config_loader.loop_issuetype_fields())) == 0
    # cache something
    with open(fake_jira.cache.issuetype_fields / f"some_file.json", "w") as f:
        f.write("{}")
    assert len(list(config_loader.loop_issuetype_fields())) == 1


@patch("mantis.jira.jira_client.requests.get")
def test_update_project_field_keys(mock_get, fake_jira: JiraClient):
    config_loader = fake_jira.system_config_loader
    if (fake_jira.cache.system / 'projects.json').exists():
        raise FileExistsError('File "projects.json" should not exist yet')
    mock_get.return_value.json.return_value = update_projects_cache_response
    got_projects = config_loader.update_projects_cache()
    assert all({int(_['id']) in list(range(10000, 10010)) + [99999] for _ in got_projects}), (
        'We expect two projects in len(update_projects_cache_response): '
        f'{len(update_projects_cache_response)} Got {[_['id'] for _ in got_projects]}')
    if not (fake_jira.cache.system / 'projects.json').exists():
        raise FileNotFoundError('File "projects.json" should have been created')

    if (fake_jira.cache.system / 'issuetypes.json').exists():
        raise FileExistsError('File "issuetypes.json" should not exist yet')
    mock_get.return_value.json.return_value = get_issuetypes_response
    got_issue_types = config_loader.get_issuetypes()
    assert all({int(_['id']) in list(range(10000, 10010)) + [99999] for _ in got_issue_types}), (
        f'Issue types: {[_['id'] for _ in got_issue_types]}')
    if not (fake_jira.cache.system / 'issuetypes.json').exists():
        raise FileNotFoundError('File "issuetypes.json" should have been created')

    mock_get.return_value.json.return_value = {"name": "Testtype"}

    if (fake_jira.cache.issuetype_fields / 'createmeta_testtype.json').exists():
        raise FileExistsError('File "createmeta_testtype.json" should not exist yet')
    allowed_types = config_loader.update_project_field_keys()
    if not (fake_jira.cache.issuetype_fields / 'createmeta_testtype.json').exists():
        raise FileNotFoundError('File "createmeta_testtype.json" should have been created')
    assert 'Testtype' in (allowed_types or []), f"Testtype not in allowed_types: {allowed_types}"
    with open(fake_jira.cache.issuetype_fields / "createmeta_testtype.json", "r") as f:
        assert f.read() == '{"name": "Testtype"}'


@patch("mantis.jira.jira_client.requests.get")
def test_compile_plugins(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = {"name": "test_type"}
    assert str(fake_jira.plugins_dir) != ".jira_cache_test"

    config_loader = fake_jira.system_config_loader

    with open(fake_jira.cache.issuetype_fields / "test_type.json", "w") as f:
        f.write('{"name": "test_type"}')

    assert (
        len(list(fake_jira.plugins_dir.iterdir())) == 0
    ), f"Not empty: {fake_jira.plugins_dir}"
    config_loader.compile_plugins()
    assert len(list(fake_jira.plugins_dir.iterdir())) == 1


def test_get_all_keys_from_nested_dicts(fake_jira: "JiraClient"):
    config_loader = fake_jira.system_config_loader
    data_in = {
        "a": ProjectFieldKeys(name="test_a", issuetype_fields=ISSUETYPEFIELDS),
        "b": ProjectFieldKeys(name="test_b", issuetype_fields=ISSUETYPEFIELDS),
    }
    data_out = config_loader.get_all_keys_from_nested_dicts(data_in)
    assert data_out


def test_print_table(fake_jira: "JiraClient", capsys):
    config_loader = fake_jira.system_config_loader
    data_in = {
        "a": ProjectFieldKeys(name="test_a", issuetype_fields=ISSUETYPEFIELDS),
        "b": ProjectFieldKeys(name="test_b", issuetype_fields=ISSUETYPEFIELDS),
    }
    data_out = config_loader.print_table(["a"], {"placeholder"}, data_in)
    assert data_out is None
    captured = capsys.readouterr()
    expected = (
        "                     - a         ",
        "placeholder          - 1         1",
        "                     - a         ",
    )
    for actual_line, expected_line in zip(captured.out.split("\n"), expected):
        assert actual_line.strip() == expected_line.strip()


def test_print_table_raises_on_non_existent_key(fake_jira: "JiraClient", capsys):
    config_loader = fake_jira.system_config_loader
    data_in = {
        "a": ProjectFieldKeys(name="test_a", issuetype_fields=ISSUETYPEFIELDS),
        "b": ProjectFieldKeys(name="test_b", issuetype_fields=ISSUETYPEFIELDS),
    }
    with pytest.raises(ValueError):
        config_loader.print_table(["non-existent"], {"placeholder"}, data_in)


def test_get_project_field_keys_from_cache(fake_jira: "JiraClient", with_fake_allowed_types):
    config_loader = fake_jira.system_config_loader
    with pytest.raises(CacheMissException):
        config_loader.get_project_field_keys_from_cache()

    fake_jira.issues._allowed_types = ["test"]
    dummy = ProjectFieldKeys(name="test_b", issuetype_fields=ISSUETYPEFIELDS)
    with open(fake_jira.cache.issuetype_fields / "createmeta_test.json", "w") as f:
        f.write(dummy.data.model_dump_json())
    from_cache = config_loader.get_project_field_keys_from_cache()
    assert from_cache


def test_inspect(fake_jira: "JiraClient"):
    config_loader = fake_jira.system_config_loader
    fake_jira.issues._allowed_types = ["test"]
    dummy = ProjectFieldKeys(name="test_b", issuetype_fields=ISSUETYPEFIELDS)
    with open(fake_jira.cache.issuetype_fields / "createmeta_test.json", "w") as f:
        f.write(dummy.data.model_dump_json())
    config_loader.inspect()
