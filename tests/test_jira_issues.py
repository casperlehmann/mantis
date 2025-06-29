import json
import re
from unittest.mock import Mock, patch

import pytest
from requests.models import HTTPError

from mantis.jira.jira_client import process_key
from mantis.jira.jira_issues import JiraIssues
from mantis.mantis_client import MantisClient
from tests.data import CacheData


class TestJiraIssues:
    def test_jira_issues_get_fake(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/ECS-1', json=CacheData().ecs_1)

        task_1 = fake_mantis.jira.issues.get("ECS-1")
        assert task_1.get("key") == "ECS-1"
        assert task_1.get("fields", {})["status"]['name'] == "In Progress"

    def test_jira_issues_get_mocked(self, fake_mantis: MantisClient, with_no_read_cache, minimal_issue_payload):
        assert fake_mantis._no_read_cache is True
        expected = minimal_issue_payload
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json = lambda: expected
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = "Description"
        with patch("requests.get", return_value=mock_response):
            task_1 = fake_mantis.jira.issues.get("TASK-1")
        assert task_1.get("key") == "TASK-1"
        assert task_1.get("fields", {}).get("status") == {"name": "resolved"}

    def test_jira_issues_get_non_existent(self, with_no_read_cache, fake_mantis: MantisClient):
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
                fake_mantis.jira.issues.get("TEST-999")
            with pytest.raises(
                ValueError,
                match="The requested issue does not exist. Note "
                'that the provided key "NONEXISTENT-1" does not '
                'appear to match your configured project "TEST"',
            ):
                fake_mantis.jira.issues.get("NONEXISTENT-1")
            with pytest.raises(
                NotImplementedError,
                match=(
                    "Partial keys are not supported. Please "
                    'provide the full key for your issue: "PROJ-11"'
                ),
            ):
                fake_mantis.jira.issues.get("11")
            with pytest.raises(
                ValueError, match=('Issue number "PROJ" in key "1-PROJ" must ' "be numeric")
            ):
                fake_mantis.jira.issues.get("1-PROJ")
            with pytest.raises(
                ValueError,
                match=re.escape("Whitespace in key is not allowed " '("PROJ-1 ")'),
            ):
                fake_mantis.jira.issues.get("PROJ-1 ")

    def test_jira_issues_create(self, fake_mantis: MantisClient, minimal_issue_payload, requests_mock):
        fake_mantis.jira.issues._allowed_types = ["Story", "Subtask", "Epic", "Bug", "Task"]
        requests_mock.post(f'{fake_mantis.http.api_url}/issue', json={'key': 'TASK-1'})
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/createmeta/{fake_mantis.jira.project_name}/issuetypes', json={'issueTypes': [{'id': '10001', 'name': 'Bug'}]})
        requests_mock.get(f'{fake_mantis.http.api_url}/project', json=[{'key': 'TEST', 'id': '1'}])
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/TASK-1', json={'key': 'TASK-1', 'fields': minimal_issue_payload['fields']})
        minimal_issue_payload['fields']['issuetype']['name'] = 'Bug'
        requests_mock.post(f'{fake_mantis.http.api_url}/issue', json=minimal_issue_payload)
        issue = fake_mantis.jira.issues.create(
            issuetype="Bug", title="Tester", data={"Summary": "a"}
        )
        fields = issue.get("fields", {})
        assert fields != {}, f"Object 'fields' is empty. Got: '{fields}' of type {type(fields)}"
        issuetype = fields.get("issuetype", {})
        assert issuetype != {}, "Object 'issuetype' is empty"
        name = issuetype.get("name")
        assert name is not None, "Expected 'name' to be present in 'issuetype'"
        assert name == "Bug", "Expected issue type name to be 'Bug'"

    def test_process_key(self, ):
        with pytest.raises(NotImplementedError):
            try:
                raise HTTPError("An excuse to raise an exception")
            except HTTPError as e:
                process_key(key="A-B-1", exception=e)

    def test_handle_http_error_raises_generic_exception(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/ECS-1', json=CacheData().ecs_1)
        mock_response = Mock()
        mock_response.reason = "Unknown error"
        mock_response.raise_for_status.side_effect = HTTPError()
        mock_response.raise_for_status.side_effect.response = (
            mock_response  # assigning itself, this is on purpose
        )
        with patch("requests.get", return_value=mock_response):
            try:
                response = fake_mantis.http._get("Task-3")
                response.raise_for_status()
            except HTTPError as e:
                assert e.response.reason == "Unknown error"
                with pytest.raises(AttributeError):
                    fake_mantis.jira.handle_http_error(exception=e, key="A-1")

    def test_jira_no_issues_fields_raises(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/ECS-1', json=CacheData().ecs_1)
        issue = fake_mantis.jira.issues.get("ECS-1")
        issue.data["fields"] = None  # type: ignore since we are purely testing that it raises an error
        with pytest.raises(KeyError):
            assert issue.fields

    def test_jira_issues_cached_issuetypes_parses_allowed_types(self, fake_mantis: MantisClient):
        cached_issuetypes = {
            "issueTypes": [
                {"id": '1', "name": "Bug", 'scope': {'project': {'id': '10000'}}},
                {"id": '2', "name": "Task", 'scope': {'project': {'id': '10000'}}}
            ]
        }
        with patch('mantis.jira.config_loader.JiraSystemConfigLoader.get_issuetypes', return_value=cached_issuetypes):
            fake_mantis.jira.issues = JiraIssues(fake_mantis.jira)
            assert fake_mantis.jira.issues._allowed_types is None
            assert fake_mantis.jira.issues.allowed_types == ["Bug", "Task"], f'Unexpected allowed types: {fake_mantis.jira.issues._allowed_types}'
            assert fake_mantis.jira.issues._allowed_types

    def test_jira_issues_get_does_write_to_cache(self, fake_mantis: MantisClient, requests_mock):
        assert fake_mantis.cache.get_issue("ECS-1") is None
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/ECS-1', json=CacheData().ecs_1)
        issue = fake_mantis.jira.issues.get("ECS-1")
        assert fake_mantis.cache.get_issue("ECS-1")
        assert len([file for file in fake_mantis.cache.issues.iterdir()]) == 1
        with open(fake_mantis.cache.issues / "ECS-1.json", "r") as f:
            data = json.load(f)
        assert data["key"] == "ECS-1"

    def test_jira_issues_get_does_retrieve_from_cache(self, fake_mantis: MantisClient, minimal_issue_payload):
        fake_mantis._no_read_cache = False
        with open(fake_mantis.cache.issues / "TASK-1.json", "w") as f:
            json.dump(minimal_issue_payload, f)
        issue = fake_mantis.jira.issues.get("TASK-1")
        assert issue.get_field("summary") == "redacted"
