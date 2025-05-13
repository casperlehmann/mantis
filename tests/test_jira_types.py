from mantis.jira.utils.jira_types import (
    IssueTypeFields,
    ProjectFieldKeys,
)


ISSUETYPEFIELDS = IssueTypeFields.model_validate(
    {
        'startAt': 1,
        'maxResults': 4,
        'total': 3,
        "fields": [{"key": "placeholder"}]
    }
)


def test_initialize_project_field_keys():
    ProjectFieldKeys(name="test", issue_type_fields=ISSUETYPEFIELDS)


def test_project_field_keys_fileds():
    project_field_keys = ProjectFieldKeys(name="test", issue_type_fields=ISSUETYPEFIELDS)
    assert isinstance(project_field_keys.fields, list)
    assert len(project_field_keys.fields) == 1
    assert project_field_keys.fields[0] == "placeholder"


def test_project_field_keys_show(capfd):
    project_field_keys = ProjectFieldKeys(name="test", issue_type_fields=ISSUETYPEFIELDS)
    assert project_field_keys.show() is None
    out, err = capfd.readouterr()
    assert out == "'placeholder'\n"
    assert err == ""
