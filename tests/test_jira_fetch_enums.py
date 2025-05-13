import inspect
import os
from unittest.mock import patch

import pytest

from mantis.jira import JiraAuth, JiraClient
from mantis.jira.utils.cache import CacheMissException
from mantis.jira.utils.jira_system_config_loader import fetch_enums
from mantis.jira.utils.jira_types import ProjectFieldKeys
from tests.data import get_issuetypes_response, update_projects_cache_response
from tests.test_jira_types import ISSUETYPEFIELDS

VAL = [
    {
        "description": "Created by Jira Agile - do not edit or delete. Issue type for a user story.",
        "id": 6,
        "untranslatedName": "Story",
    },
    {
        "description": "A small piece of work that's part of a larger task.",
        "id": 18,
        "untranslatedName": "Sub-Task",
    },
    {
        "description": "A collection of related bugs, stories, and tasks.",
        "id": 5,
        "untranslatedName": "Epic",
    },
    {"description": "A problem or error.", "id": 1, "untranslatedName": "Bug"},
    {
        "description": "A small, distinct piece of work.",
        "id": 3,
        "untranslatedName": "Task",
    },
    {
        "description": "A new feature of the product, which has yet to be developed.",
        "id": 17,
        "untranslatedName": "New Feature",
    },
    {
        "description": "Service Impacting Event",
        "id": 10,
        "untranslatedName": "Incident",
    },
]


@patch("mantis.jira.jira_client.requests.get")
def test_fetch_issuetype_enums_mock(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = VAL
    types_filter = lambda d: int(d["id"]) < 100 and d["name"] in (
        "Bug",
        "Task",
        "Epic",
        "Story",
        "Incident",
        "New Feature",
        "Sub-Task",
    )
    mapping = {"id": "id", "description": "description", "untranslatedName": "name"}
    caster_functions = {"id": int}
    issue_enums = fetch_enums(
        fake_jira,
        endpoint="issuetype",
        filter=types_filter,
        mapping=mapping,
        caster_functions=caster_functions,
    )
    assert (
        len(issue_enums) == 7
    ), f"Exactly seven matches the filter: {str(inspect.getsource(types_filter)).strip()}"
    issue_type_1_bugs = [_ for _ in issue_enums if _["id"] == 1]
    assert len(issue_type_1_bugs) == 1, f"Exactly one with id == 1"
    issue_type_1_bug = issue_type_1_bugs[0]
    assert issue_type_1_bug["name"] == "Bug", "Issue of id == 1 has wrong name"
    assert (
        issue_type_1_bug["description"] == "A problem or error."
    ), "Issue of id == 1 has wrong description"


@patch("mantis.jira.jira_client.requests.get")
def test_fetch_issuetype_enums_mock_no_casting(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = VAL
    types_filter = lambda d: d["id"] == 1
    mapping = {"id": "id", "description": "description", "untranslatedName": "name"}
    caster_functions = {}
    issue_enums = fetch_enums(
        fake_jira,
        endpoint="issuetype",
        filter=types_filter,
        mapping=mapping,
        caster_functions=caster_functions,
    )
    assert (
        len(issue_enums) == 1
    ), f"Exactly one matches the filter: {str(inspect.getsource(types_filter)).strip()}"
    issue_type_1_bug = issue_enums[0]
    assert issue_type_1_bug["name"] == "Bug", "Issue of id == '1' has wrong name"
    assert (
        issue_type_1_bug["description"] == "A problem or error."
    ), "Issue of id == '1' has wrong description"


@patch("mantis.jira.jira_client.requests.get")
def test_fetch_issuetype_enums_mock_no_mapping(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = VAL
    types_filter = lambda d: d["id"] == 1
    mapping = {}
    caster_functions = {}
    issue_enums = fetch_enums(
        fake_jira,
        endpoint="issuetype",
        filter=types_filter,
        mapping=mapping,
        caster_functions=caster_functions,
    )
    assert (
        len(issue_enums) == 1
    ), f"Exactly one matches the filter: {str(inspect.getsource(types_filter)).strip()}"
    issue_type_1_bug = issue_enums[0]
    assert (
        issue_type_1_bug["untranslatedName"] == "Bug"
    ), "Issue of id == '1' has wrong untranslatedName"


@pytest.mark.skipif(
    not os.path.exists("options.toml"), reason='File "options.toml" does not exist'
)
@pytest.mark.skipif(
    not os.getenv("EXECUTE_SKIPPED"), reason="This is a live test against the Jira api"
)
def test_fetch_issuetype_enums_real(jira_client_from_user_toml):
    types_filter = lambda d: int(d["id"]) < 100 and d["name"] in (
        "Bug",
        "Task",
        "Epic",
        "Story",
        "Incident",
        "New Feature",
        "Sub-Task",
    )
    mapping = {"id": "id", "description": "description", "untranslatedName": "name"}
    caster_functions = {"id": int}
    issue_enums = fetch_enums(
        jira_client_from_user_toml,
        endpoint="issuetype",
        filter=types_filter,
        mapping=mapping,
        caster_functions=caster_functions,
    )
    assert (
        len(issue_enums) == 7
    ), f"Exactly seven matches the filter: {str(inspect.getsource(types_filter)).strip()}"
    issue_type_1_bugs = [_ for _ in issue_enums if _["id"] == 1]
    assert len(issue_type_1_bugs) == 1, f"Exactly one with id == 1"
    issue_type_1_bug = issue_type_1_bugs[0]
    assert issue_type_1_bug["name"] == "Bug", "Issue of id == 1 has wrong name"
    assert (
        issue_type_1_bug["description"] == "A problem or error."
    ), "Issue of id == 1 has wrong description"


@pytest.mark.skipif(
    not os.path.exists("options.toml"), reason='File "options.toml" does not exist'
)
@pytest.mark.skipif(
    not os.getenv("EXECUTE_SKIPPED"), reason="This is a live test against the Jira api"
)
def test_fetch_issuetype_enums_real_no_casting(jira_client_from_user_toml):
    types_filter = lambda d: d["id"] == "1"
    mapping = {"id": "id", "description": "description", "untranslatedName": "name"}
    caster_functions = {}
    issue_enums = fetch_enums(
        jira_client_from_user_toml,
        endpoint="issuetype",
        filter=types_filter,
        mapping=mapping,
        caster_functions=caster_functions,
    )
    assert (
        len(issue_enums) == 1
    ), f"Exactly one matches the filter: {str(inspect.getsource(types_filter)).strip()}"
    issue_type_1_bug = issue_enums[0]
    assert issue_type_1_bug["name"] == "Bug", "Issue of id == '1' has wrong name"
    assert (
        issue_type_1_bug["description"] == "A problem or error."
    ), "Issue of id == '1' has wrong description"


@patch("mantis.jira.jira_client.requests.get")
def test_config_loader_update_issuetypes_writes_to_cache(
    mock_get, fake_jira: JiraClient
):
    mock_get.return_value.json.return_value = get_issuetypes_response
    config_loader = fake_jira.system_config_loader
    assert (
        len(list(fake_jira.cache.system.iterdir())) == 1
    ), f"Not empty: {fake_jira.cache.system}"

    config_loader.update_issuetypes_cache()
    assert (
        len(list(fake_jira.cache.system.iterdir())) == 2
    ), f"Not empty: {fake_jira.cache.system}"


@patch("mantis.jira.jira_client.requests.get")
def test_config_loader_get_issuetypes_names_from_cache(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = get_issuetypes_response
    config_loader = fake_jira.system_config_loader
    with open(fake_jira.cache.system / "issue_types.json", "w") as f:
        f.write('{"a": "b"}')
    retrieved = config_loader.get_issuetypes_names_from_cache()
    assert retrieved == {"a": "b"}


@patch("mantis.jira.jira_client.requests.get")
def test_config_loader_loop_yields_files(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = get_issuetypes_response
    config_loader = fake_jira.system_config_loader
    assert len(list(config_loader.loop_issue_type_fields())) == 0
    # cache something
    with open(
        fake_jira.cache.system / f"issue_type_fields/some_file.json",
        "w",
    ) as f:
        f.write("{}")
    assert len(list(config_loader.loop_issue_type_fields())) == 1


@patch("mantis.jira.jira_client.requests.get")
def test_update_project_field_keys(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = {"name": "test_type"}
    config_loader = fake_jira.system_config_loader
    config_loader.client.issues.allowed_types = ["test_type"]
    allowed_types = config_loader.update_project_field_keys()
    assert allowed_types == ["test_type"]
    with open(fake_jira.cache.issue_type_fields / "test_type.json", "r") as f:
        assert f.read() == '{"name": "test_type"}'


@patch("mantis.jira.jira_client.requests.get")
def test_compile_plugins(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = {"name": "test_type"}
    assert str(fake_jira.plugins_dir) != ".jira_cache_test"

    config_loader = fake_jira.system_config_loader

    with open(fake_jira.cache.issue_type_fields / "test_type.json", "w") as f:
        f.write('{"name": "test_type"}')

    assert (
        len(list(fake_jira.plugins_dir.iterdir())) == 0
    ), f"Not empty: {fake_jira.plugins_dir}"
    config_loader.compile_plugins()
    assert len(list(fake_jira.plugins_dir.iterdir())) == 1


def test_get_all_keys_from_nested_dicts(
    fake_jira: "JiraClient",
):
    config_loader = fake_jira.system_config_loader
    data_in = {
        "a": ProjectFieldKeys(name="test_a", issue_type_fields=ISSUETYPEFIELDS),
        "b": ProjectFieldKeys(name="test_b", issue_type_fields=ISSUETYPEFIELDS),
    }
    data_out = config_loader.get_all_keys_from_nested_dicts(data_in)
    assert data_out


def test_print_table(fake_jira: "JiraClient", capsys):
    config_loader = fake_jira.system_config_loader
    data_in = {
        "a": ProjectFieldKeys(name="test_a", issue_type_fields=ISSUETYPEFIELDS),
        "b": ProjectFieldKeys(name="test_b", issue_type_fields=ISSUETYPEFIELDS),
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
        "a": ProjectFieldKeys(name="test_a", issue_type_fields=ISSUETYPEFIELDS),
        "b": ProjectFieldKeys(name="test_b", issue_type_fields=ISSUETYPEFIELDS),
    }
    with pytest.raises(ValueError):
        config_loader.print_table(["non-existent"], {"placeholder"}, data_in)


def test_get_project_field_keys_from_cache(fake_jira: "JiraClient"):
    config_loader = fake_jira.system_config_loader
    with pytest.raises(CacheMissException):
        config_loader.get_project_field_keys_from_cache()

    fake_jira.issues.allowed_types = ["test"]
    dummy = ProjectFieldKeys(name="test_b", issue_type_fields=ISSUETYPEFIELDS)
    with open(fake_jira.cache.issue_type_fields / "test.json", "w") as f:
        f.write(dummy.data.model_dump_json())
    from_cache = config_loader.get_project_field_keys_from_cache()
    assert from_cache


def test_inspect(fake_jira: "JiraClient"):
    config_loader = fake_jira.system_config_loader
    fake_jira.issues.allowed_types = ["test"]
    dummy = ProjectFieldKeys(name="test_b", issue_type_fields=ISSUETYPEFIELDS)
    with open(fake_jira.cache.issue_type_fields / "test.json", "w") as f:
        f.write(dummy.data.model_dump_json())
    config_loader.inspect()
