import os
import re
from unittest.mock import Mock, patch

import pytest
from requests.models import HTTPError

from mantis.jira import JiraAuth, JiraClient


@pytest.fixture
def fake_jira(opts_from_fake_cli, mock_get_request):
    expected = {"key": "TASK-1", "fields": {"status": {"name": "resolved"}}}
    mock_get_request.return_value.json.return_value = expected
    auth = JiraAuth(opts_from_fake_cli)
    return JiraClient(opts_from_fake_cli, auth)


def test_jira_issues_get_fake(fake_jira):
    task_1 = fake_jira.issues.get("TASK-1")
    assert task_1.get("key") == "TASK-1"
    assert task_1.get("fields", {}).get("status") == {"name": "resolved"}


def test_jira_issues_get_mocked(fake_jira: JiraClient, with_no_cache):
    assert fake_jira._no_cache is True
    expected = {"key": "TASK-1", "fields": {"status": {"name": "resolved"}}}
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


def test_jira_issues_get_non_existent(with_no_cache, fake_jira: JiraClient):
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


@pytest.mark.skipif(
    not os.path.exists("options.toml"), reason='File "options.toml" does not exist'
)
@pytest.mark.skipif(
    not os.getenv("EXECUTE_SKIPPED"), reason="This is a live test against the Jira api"
)
def test_jira_issues_get_real(jira_client_from_user_toml):
    test_3 = jira_client_from_user_toml.issues.get("TEST-3")
    assert test_3.get("key") == "TEST-3"
    test_3_fields = test_3.get("fields", {})
    assert test_3_fields != {}
    test_3_status = test_3_fields.get("status", {})
    assert test_3_status != {}
    test_3_status_name = test_3_status.get("name", {})
    assert test_3_status_name == "In Progress"


def test_jira_issues_create(fake_jira, mock_post_request):
    with pytest.raises(ValueError):
        issue = fake_jira.issues.create(issue_type="Bug", title="Tester", data={})
    expected = {
        "key": "TASK-1",
        "fields": {"status": {"name": "In Progress"}, "issuetype": {"name": "Bug"}},
    }
    mock_post_request.return_value.json.return_value = expected
    issue = fake_jira.issues.create(
        issue_type="Bug", title="Tester", data={"Summary": "a"}
    )
    fields = issue.get("fields", {})
    assert fields != {}, "Object 'fields' is empty"
    issuetype = fields.get("issuetype", {})
    assert issuetype != {}, "Object 'issuetype' is empty"
    name = issuetype.get("name")
    assert name is not None, "Expected 'name' to be present in 'issuetype'"
    assert name == "Bug", "Expected issue type name to be 'Bug'"
