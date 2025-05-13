import inspect
import json
import os
from unittest.mock import patch

import pytest

from mantis.jira import JiraAuth, JiraClient
from mantis.jira.utils.cache import CacheMissException
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
def test_cache_get_issuetypes_from_system_cache(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = get_issuetypes_response
    cache = fake_jira.cache
    with open(fake_jira.cache.system / "issuetypes.json", "w") as f:
        f.write('[{"a": "b"}]')
    retrieved = cache.get_issuetypes_from_system_cache()
    assert retrieved == [{"a": "b"}]


@patch("mantis.jira.jira_client.requests.get")
def test_config_loader_loop_yields_files(mock_get, fake_jira: JiraClient):
    mock_get.return_value.json.return_value = get_issuetypes_response
    config_loader = fake_jira.system_config_loader
    assert len(list(config_loader.loop_issuetype_fields())) == 0
    # cache something
    with open(
        fake_jira.cache.system / f"issue_type_fields/some_file.json",
        "w",
    ) as f:
        f.write("{}")
    assert len(list(config_loader.loop_issuetype_fields())) == 1


@patch("mantis.jira.jira_client.requests.get")
def test_update_project_field_keys(mock_get, fake_jira: JiraClient):
    config_loader = fake_jira.system_config_loader

    if (fake_jira.cache.system / 'projects.json').exists():
        raise FileExistsError('File "projects.json" should not exist yet')
    mock_get.return_value.json.return_value = update_projects_cache_response
    got_projects = config_loader.update_projects_cache()
    assert all({int(_['id']) in list(range(10000, 10010)) + [99999] for _ in got_projects}), f'We expect two projects in len(update_projects_cache_response): {len(update_projects_cache_response)} Got {[_['id'] for _ in got_projects]}'
    if not (fake_jira.cache.system / 'projects.json').exists():
        raise FileNotFoundError('File "projects.json" should have been created')

    if (fake_jira.cache.system / 'issuetypes.json').exists():
        raise FileExistsError('File "issuetypes.json" should not exist yet')
    mock_get.return_value.json.return_value = get_issuetypes_response
    got_issue_types = config_loader.get_issuetypes()
    assert all({int(_['id']) in list(range(10000, 10010)) + [99999] for _ in got_issue_types}), f'Issue types: {[_['id'] for _ in got_issue_types]}'
    if not (fake_jira.cache.system / 'issuetypes.json').exists():
        raise FileNotFoundError('File "issuetypes.json" should have been created')

    mock_get.return_value.json.return_value = {"name": "Testtype"}
    # config_loader.client.issues.allowed_types = ["Testtype"]

    # assert cache.get_issuetypes_from_system_cache() == '', f'||| {cache.get_issuetypes_from_system_cache()}'

    if (fake_jira.cache.issuetype_fields / 'createmeta_testtype.json').exists():
        raise FileExistsError('File "createmeta_testtype.json" should not exist yet')
    fake_jira._no_read_cache = False
    allowed_types = config_loader.update_project_field_keys()
    fake_jira._no_read_cache = True
    if not (fake_jira.cache.issuetype_fields / 'createmeta_testtype.json').exists():
        raise FileNotFoundError('File "createmeta_testtype.json" should have been created')
    assert 'Testtype' in (allowed_types or []), f"Testtype not in allowed_types: {allowed_types}"
    fake_jira._no_read_cache = False
    with open(fake_jira.cache.issuetype_fields / "createmeta_testtype.json", "r") as f:
        assert f.read() == '{"name": "Testtype"}'
    fake_jira._no_read_cache = True

# @patch("mantis.jira.jira_client.requests.get")
# def test_get_issuetypes(mock_get, fake_jira: JiraClient):
#     # response.json() if _.get('scope', {}).get('project', {}).get('id') == project['id']]
#     # [{"expand":"description,lead,issueTypes,url,projectKeys,permissions,insight","self":"https://caspertestaccount.atlassian.net/rest/api/3/project/10001","id":"10001","key":"LEARNJIRA","name":"(Learn) Jira Premium benefits in 5 min 👋","avatarUrls":{"48x48":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10407","24x24":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10407?size=small","16x16":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10407?size=xsmall","32x32":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10407?size=medium"},"projectTypeKey":"software","simplified":True,"style":"next-gen","isPrivate":False,"properties":{},"entityId":"fba6ffc9-d429-408f-8495-00edce965d92","uuid":"fba6ffc9-d429-408f-8495-00edce965d92"},{"expand":"description,lead,issueTypes,url,projectKeys,permissions,insight","self":"https://caspertestaccount.atlassian.net/rest/api/3/project/10000","id":"10000","key":"ECS","name":"E-Commerce Checkout System","avatarUrls":{"48x48":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10417","24x24":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10417?size=small","16x16":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10417?size=xsmall","32x32":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10417?size=medium"},"projectTypeKey":"software","simplified":True,"style":"next-gen","isPrivate":False,"properties":{},"entityId":"f853ead8-876c-46a8-9dbe-6479d9f03449","uuid":"f853ead8-876c-46a8-9dbe-6479d9f03449"}]
#     config_loader = fake_jira.system_config_loader # No http
#     mock_get.return_value.json.return_value = [{"expand":"description,lead,issueTypes,url,projectKeys,permissions,insight","self":"https://caspertestaccount.atlassian.net/rest/api/3/project/10001","id":"10001","key":"LEARNJIRA","name":"(Learn) Jira Premium benefits in 5 min 👋","avatarUrls":{"48x48":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10407","24x24":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10407?size=small","16x16":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10407?size=xsmall","32x32":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10407?size=medium"},"projectTypeKey":"software","simplified":True,"style":"next-gen","isPrivate":False,"properties":{},"entityId":"fba6ffc9-d429-408f-8495-00edce965d92","uuid":"fba6ffc9-d429-408f-8495-00edce965d92"},{"expand":"description,lead,issueTypes,url,projectKeys,permissions,insight","self":"https://caspertestaccount.atlassian.net/rest/api/3/project/10000","id":"10000","key":"ECS","name":"E-Commerce Checkout System","avatarUrls":{"48x48":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10417","24x24":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10417?size=small","16x16":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10417?size=xsmall","32x32":"https://caspertestaccount.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/10417?size=medium"},"projectTypeKey":"software","simplified":True,"style":"next-gen","isPrivate":False,"properties":{},"entityId":"f853ead8-876c-46a8-9dbe-6479d9f03449","uuid":"f853ead8-876c-46a8-9dbe-6479d9f03449"}]
#     assert config_loader.update_projects_cache()# == {'name': 'test_type'}
#     mock_get.return_value.json.return_value = {'name': 'test_type'}
#     config_loader.client.issues.allowed_types = ["test_type"]
#     issue_types = config_loader.get_issuetypes()
#     assert issue_types == ["test_type"]
#     # with open(fake_jira.cache.issue_type_fields / "createmeta_test_type.json", "r") as f:
#     # assert f.read() == '{"name": "test_type"}'

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


def test_get_project_field_keys_from_cache(fake_jira: "JiraClient", with_fake_allowed_types):
    config_loader = fake_jira.system_config_loader
    with pytest.raises(CacheMissException):
        config_loader.get_project_field_keys_from_cache()

    fake_jira.issues._allowed_types = ["test"]
    dummy = ProjectFieldKeys(name="test_b", issue_type_fields=ISSUETYPEFIELDS)
    with open(fake_jira.cache.issuetype_fields / "createmeta_test.json", "w") as f:
        f.write(dummy.data.model_dump_json())
    from_cache = config_loader.get_project_field_keys_from_cache()
    assert from_cache


def test_inspect(fake_jira: "JiraClient"):
    config_loader = fake_jira.system_config_loader
    fake_jira.issues._allowed_types = ["test"]
    dummy = ProjectFieldKeys(name="test_b", issue_type_fields=ISSUETYPEFIELDS)
    with open(fake_jira.cache.issuetype_fields / "createmeta_test.json", "w") as f:
        f.write(dummy.data.model_dump_json())
    config_loader.inspect()
