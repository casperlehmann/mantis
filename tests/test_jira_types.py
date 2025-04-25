import pytest

from mantis.jira.utils.jira_types import (
    IssueType,
    IssueTypeFields,
    Project,
    ProjectFieldKeys,
)

ISSUETYPE = {
    "id": "1",
    "description": "placeholder",
    "iconUrl": "placeholder",
    "name": "placeholder",
    "untranslatedName": "placeholder",
    "subtask": "False",
    "hierarchyLevel": 1,
    "expand": "placeholder",
    "fields": {"placeholder": "placeholder"},
}
PROJECT = {
    "issuetypes": [ISSUETYPE],
    "expand": "placeholder",
    "id": "placeholder",
    "key": "placeholder",
    "name": "placeholder",
    "avatarUrls": {"placeholder": "placeholder"},
}
ISSUETYPEFIELDS: IssueTypeFields = {"projects": [PROJECT], "expand": "placeholder"}


def test_initialize_project_field_keys():
    ProjectFieldKeys(name="test", data=ISSUETYPEFIELDS)


def test_project_field_keys_fileds():
    project_field_keys = ProjectFieldKeys(name="test", data=ISSUETYPEFIELDS)
    assert isinstance(project_field_keys.fields, list)
    assert len(project_field_keys.fields) == 1
    assert project_field_keys.fields[0] == "placeholder"


def test_project_field_keys_show(capfd):
    project_field_keys = ProjectFieldKeys(name="test", data=ISSUETYPEFIELDS)
    assert project_field_keys.show() is None
    out, err = capfd.readouterr()
    assert out == "'placeholder'\n"
    assert err == ""
