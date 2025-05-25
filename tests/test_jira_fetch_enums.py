import json
from typing import Any
from unittest.mock import patch

import pytest

from mantis.jira import JiraClient
from mantis.jira.utils.cache import CacheMissException
from mantis.jira.utils.jira_system_config_loader import Inspector
from tests.data import get_issuetypes_response, update_projects_cache_response, CacheData


@patch("mantis.jira.jira_client.requests.get")
def test_config_loader_update_issuetypes_writes_to_cache(
    mock_get, fake_jira: JiraClient
):
    mock_get.return_value.json.return_value = get_issuetypes_response
    config_loader = fake_jira.system_config_loader
    set_with_no_issuetypes = {str(_).split('/')[-1] for _ in fake_jira.cache.system.iterdir()}
    assert set_with_no_issuetypes == {'createmeta', 'editmeta'}, (
        f"System cache expected 2 values. Got: {set_with_no_issuetypes}")

    config_loader.get_issuetypes(force_skip_cache = True)
    set_with_issuetypes = {str(_).split('/')[-1] for _ in fake_jira.cache.system.iterdir()}
    assert set_with_issuetypes == {'createmeta', 'editmeta', 'issuetypes.json'}, (
        f"System cache expected 3 values. Got: {fake_jira.cache.system}")

def test_persisted_issuetypes_data():
    cache_data = CacheData()
    assert hasattr(cache_data, 'issuetypes')
    selector = lambda field_name: {_[field_name] for _ in cache_data.issuetypes.get("issueTypes")}
    assert len(cache_data.issuetypes.get("issueTypes")) == 5
    assert selector('name') == {'Subtask', 'Story', 'Bug', 'Task', 'Epic'}


@patch("mantis.jira.jira_client.requests.get")
def test_cache_get_issuetypes_from_system_cache(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = get_issuetypes_response
    cache = fake_jira.cache
    with open(fake_jira.cache.system / "issuetypes.json", "w") as f:
        json.dump(CacheData().issuetypes, f)
    retrieved = cache.get_issuetypes_from_system_cache()
    assert retrieved
    assert retrieved['issueTypes'][0].get("description") in (
            "Subtasks track small pieces of work that are part of a larger task.",
            "Epics track collections of related bugs, stories, and tasks."
        ), (
            f'retrieved: {retrieved}'
        )


@patch("mantis.jira.jira_client.requests.get")
def test_config_loader_loop_yields_files(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = get_issuetypes_response
    config_loader = fake_jira.system_config_loader
    assert len(list(config_loader.loop_createmeta())) == 0
    # cache something
    with open(fake_jira.cache.createmeta / f"some_file.json", "w") as f:
        f.write("{}")
    assert len(list(config_loader.loop_createmeta())) == 1


@patch("mantis.jira.jira_client.requests.get")
def test_update_project_field_keys(mock_get, fake_jira: JiraClient):
    config_loader = fake_jira.system_config_loader

    # Mock projects response
    mock_get.return_value.json.return_value = update_projects_cache_response

    # Test initial state
    if (fake_jira.cache.system / 'projects.json').exists():
        raise FileExistsError('File "projects.json" should not exist yet')
    assert fake_jira._project_id == None

    # Fetch and cache projects data (without updating the object)
    got_projects = config_loader.get_projects(force_skip_cache = True)
    assert isinstance(got_projects, list)
    assert len(got_projects) == 2
    assert {_['id'] for _ in got_projects} == {'10000', '10001'}

    # Check side-effect
    if not (fake_jira.cache.system / 'projects.json').exists():
        raise FileNotFoundError('File "projects.json" should have been created')
    # Note: Private jira._project_id is still None, even after the file has been written.
    assert fake_jira._project_id == None
    # Note: Only once the public jira.project_id is queried does the private one get updated
    assert fake_jira.project_id == '10000'
    assert fake_jira._project_id == '10000'
    
    # Test projects response
    got_project_ids_as_ints = {int(_['id']) for _ in got_projects}
    expected_project_ids = {10000, 10001}
    assert got_project_ids_as_ints == expected_project_ids, (
        'We expect two projects in len(update_projects_cache_response): '
        f'{len(update_projects_cache_response)} Got {got_project_ids_as_ints}')
    
    # Mock issuetypes response
    mock_get.return_value.json.return_value = CacheData().issuetypes

    # Fetch and cache issuetypes data
    if (fake_jira.cache.system / 'issuetypes.json').exists():
        raise FileExistsError('File "issuetypes.json" should not exist yet')
    got_issue_types = config_loader.get_issuetypes()
    assert isinstance(got_issue_types, dict)
    assert 'issueTypes' in got_issue_types
    assert isinstance(got_issue_types['issueTypes'], list)
    expected_issue_ids: set[int] = set(list(range(10001, 10006)))
    got_issue_ids_as_ints = {int(_['id']) for _ in got_issue_types['issueTypes']}

    assert len(got_issue_types['issueTypes']) == 5 #, f'{len(got_issue_types)} {got_issue_types}'
    assert got_issue_ids_as_ints == expected_issue_ids, (
        f'Issue types: {got_issue_ids_as_ints}')
    if not (fake_jira.cache.system / 'issuetypes.json').exists():
        raise FileNotFoundError('File "issuetypes.json" should have been created')

    mock_get.return_value.json.return_value = {'fields': []}

    if (fake_jira.cache.createmeta / 'createmeta_story.json').exists():
        raise FileExistsError('File "createmeta_story.json" should not exist yet')
    allowed_types = config_loader.fetch_and_update_all_createmeta()
    assert set(allowed_types) == set(['Epic', 'Subtask', 'Task', 'Story', 'Bug'])
    if not (fake_jira.cache.createmeta / 'createmeta_story.json').exists():
        raise FileNotFoundError('File "createmeta_story.json" should have been created')
    assert 'Story' in allowed_types, f"Testtype not in allowed_types: {allowed_types}"
    with open(fake_jira.cache.createmeta / "createmeta_story.json", "r") as f:
        assert f.read() == '{"fields": []}'


@patch("mantis.jira.jira_client.requests.get")
def test_compile_plugins(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = {"name": "Testtype"}
    assert str(fake_jira.plugins_dir) != ".jira_cache_test"

    config_loader = fake_jira.system_config_loader

    with open(fake_jira.cache.createmeta / "Testtype.json", "w") as f:
        f.write('{"name": "Testtype"}')

    assert (
        len(list(fake_jira.plugins_dir.iterdir())) == 0
    ), f"Not empty: {fake_jira.plugins_dir}"
    config_loader.compile_plugins()
    assert len(list(fake_jira.plugins_dir.iterdir())) == 1


def test_print_table(fake_jira: "JiraClient", capsys):
    column_order: list[str] = ["a"]
    all_field_keys: set[str] = {"placeholder"}
    issuetype_field_map: dict[str, Any] = {'a': {'placeholder':''}}
    data_out = Inspector.print_table(column_order, all_field_keys, issuetype_field_map)
    assert data_out is None
    captured = capsys.readouterr()
    expected = (
        "                     - a         ",
        "placeholder          - 1         ",
        "                     - a         ",
    )
    for actual_line, expected_line in zip(captured.out.split("\n"), expected):
        assert actual_line.strip() == expected_line.strip()


def test_print_table_raises_on_non_existent_key(fake_jira: "JiraClient", capsys):
    column_order: list[str] = ["a"]
    all_field_keys: set[str] = {"placeholder"}
    issuetype_field_map: dict[str, Any] = {'a': {'placeholder':''}}
    _ = Inspector.print_table(column_order, all_field_keys, issuetype_field_map)
    with pytest.raises(ValueError):
        Inspector.print_table(["non-existent"], {"placeholder"}, issuetype_field_map)


def test_get_project_field_keys_from_cache(fake_jira: "JiraClient", with_fake_allowed_types):
    with pytest.raises(CacheMissException):
        Inspector.get_createmeta_models(fake_jira)

    fake_jira.issues._allowed_types = ["test"]
    from tests.data import CacheData
    data = CacheData().createmeta_epic
    with open(fake_jira.cache.createmeta / "createmeta_test.json", "w") as f:
        json.dump(data, f)
    from_cache = Inspector.get_createmeta_models(fake_jira)
    assert from_cache
