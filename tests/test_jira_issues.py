import json
import os
import re
from unittest.mock import Mock, patch

import pytest
from requests.models import HTTPError

from mantis.jira import JiraClient
from mantis.jira.jira_client import process_key
from mantis.jira.jira_issues import JiraIssues


def test_jira_issues_get_fake(fake_jira: JiraClient):
    task_1 = fake_jira.issues.get("TASK-1")
    assert task_1.get("key") == "TASK-1"
    assert task_1.get("fields", {}).get("status") == {"name": "resolved"}  # type: ignore None risk of second get. Since it's explicitly returning a dict as default.


def test_jira_issues_get_mocked(fake_jira: JiraClient, with_no_read_cache):
    assert fake_jira._no_read_cache is True
    expected = {"key": "TASK-1", "fields": {"status": {"name": "resolved"}, "description": "redacted"}}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json = lambda: expected
    mock_response.headers = {"Content-Type": "text/plain"}
    mock_response.text = "Description"
    with patch("requests.get", return_value=mock_response):
        task_1 = fake_jira.issues.get("TASK-1")
    assert task_1.get("key") == "TASK-1"
    assert task_1.get("fields", {}).get("status") == {"name": "resolved"}


def test_jira_issues_get_non_existent(with_no_read_cache, fake_jira: JiraClient):
    mock_response = Mock()
    mock_response.reason = "Not Found"
    mock_response.raise_for_status.side_effect = HTTPError()
    mock_response.raise_for_status.side_effect.response = (
        mock_response  # assigning itself, this is on purpose
    )
    with patch("requests.get", return_value=mock_response):
        with pytest.raises(
            ValueError,
            match=('The issue "TEST-999" does not exists in ' 'the project "TEST"'),
        ):
            fake_jira.issues.get("TEST-999")
        with pytest.raises(
            ValueError,
            match="The requested issue does not exist. Note "
            'that the provided key "NONEXISTENT-1" does not '
            'appear to match your configured project "TEST"',
        ):
            fake_jira.issues.get("NONEXISTENT-1")
        with pytest.raises(
            NotImplementedError,
            match=(
                "Partial keys are not supported. Please "
                'provide the full key for your issue: "PROJ-11"'
            ),
        ):
            fake_jira.issues.get("11")
        with pytest.raises(
            ValueError, match=('Issue number "PROJ" in key "1-PROJ" must ' "be numeric")
        ):
            fake_jira.issues.get("1-PROJ")
        with pytest.raises(
            ValueError,
            match=re.escape("Whitespace in key is not allowed " '("PROJ-1 ")'),
        ):
            fake_jira.issues.get("PROJ-1 ")


@patch("mantis.jira.jira_client.requests.post")
def test_jira_issues_create(mock_post, fake_jira: JiraClient, with_fake_allowed_types):
    mock_post.return_value.json.return_value = {}
    with pytest.raises(ValueError):
        issue = fake_jira.issues.create(issuetype="Bug", title="Tester", data={})
    expected = {
        "key": "TASK-1",
        "fields": {"status": {"name": "In Progress"}, "issuetype": {"name": "Bug"}},
    }
    mock_post.return_value.json.return_value = expected
    issue = fake_jira.issues.create(
        issuetype="Bug", title="Tester", data={"Summary": "a"}
    )
    fields = issue.get("fields", {})
    assert fields != {}, "Object 'fields' is empty"
    issuetype = fields.get("issuetype", {})
    assert issuetype != {}, "Object 'issuetype' is empty"
    name = issuetype.get("name")
    assert name is not None, "Expected 'name' to be present in 'issuetype'"
    assert name == "Bug", "Expected issue type name to be 'Bug'"


def test_process_key():
    with pytest.raises(NotImplementedError):
        try:
            raise HTTPError("An excuse to raise an exception")
        except HTTPError as e:
            process_key(key="A-B-1", exception=e)


def test_handle_http_error_raises_generic_exception(
    fake_jira: "JiraClient", mock_post_request
):
    mock_response = Mock()
    mock_response.reason = "Unknown error"
    mock_response.raise_for_status.side_effect = HTTPError()
    mock_response.raise_for_status.side_effect.response = (
        mock_response  # assigning itself, this is on purpose
    )
    with patch("requests.get", return_value=mock_response):
        try:
            response = fake_jira._get("Task-3")
            response.raise_for_status()
        except HTTPError as e:
            assert e.response.reason == "Unknown error"
            with pytest.raises(AttributeError):
                fake_jira.issues.handle_http_error(exception=e, key="A-1")


def test_jira_no_issues_fields_raises(fake_jira: JiraClient, mock_post_request):
    issue = fake_jira.issues.get("TASK-1")
    issue.data["fields"] = None  # type: ignore since we are purely testing that it raises an error
    with pytest.raises(KeyError):
        assert issue.fields


def test_jira_issues_cached_issuetypes_parses_allowed_types(fake_jira: JiraClient):
    cached_issuetypes = {
        "issueTypes": [
            {"id": '1', "name": "Bug", 'scope': {'project': {'id': '10000'}}},
            {"id": '2', "name": "Task", 'scope': {'project': {'id': '10000'}}}
        ]
    }
    fake_jira.system_config_loader.get_issuetypes_for_project = (
        lambda *args, **kwargs: cached_issuetypes
    )
    fake_jira.issues = JiraIssues(fake_jira)
    assert fake_jira.issues._allowed_types is None
    assert fake_jira.issues.allowed_types == ["Bug", "Task"], f'Unexpected allowed types: {fake_jira.issues._allowed_types}'
    assert fake_jira.issues._allowed_types

def test_jira_issues_get_does_write_to_cache(fake_jira: JiraClient):
    assert fake_jira.cache.get_issue("TASK-1") is None
    assert len([file for file in fake_jira.cache.issues.iterdir()]) == 0
    issue = fake_jira.issues.get("TASK-1")
    assert fake_jira.cache.get_issue("TASK-1")
    assert len([file for file in fake_jira.cache.issues.iterdir()]) == 1
    with open(fake_jira.cache.issues / "TASK-1.json", "r") as f:
        data = json.load(f)
    assert data == {"fields": {"status": {"name": "resolved"}, "description": "redacted"}, "key": "TASK-1"}


def test_jira_issues_get_does_retrieve_from_cache(fake_jira: JiraClient):
    fake_jira._no_read_cache = False
    data = {"key": "TASK-1", "redacted": "True", "fields": {"status": {"name": "resolved"}, "description": "redacted"}}
    with open(fake_jira.cache.issues / "TASK-1.json", "w") as f:
        json.dump(data, f)
    issue = fake_jira.issues.get("TASK-1")
    assert issue.get("redacted") == "True"
