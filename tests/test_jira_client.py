from unittest.mock import patch

import pytest
import requests

from mantis.jira import JiraClient


def test_test_auth_complains_with_bad_input(requests_mock, fake_jira: JiraClient, capsys):
    api_url = fake_jira.options.url + "/rest/api/latest"
    requests_mock.get(f'{api_url}/myself', json={})
    fake_jira.test_auth()
    captured = capsys.readouterr()
    assert captured.out == ("Connected as user: ERROR: No displayName\n")
    assert captured.err == ""


def test_test_auth_informs_login(requests_mock, fake_jira: JiraClient, capsys):
    api_url = fake_jira.options.url + "/rest/api/latest"
    requests_mock.get(f'{api_url}/myself', json={'displayName': 'Buddy'})
    fake_jira.test_auth()
    captured = capsys.readouterr()
    assert captured.out == ("Connected as user: Buddy\n")
    assert captured.err == ""


def test_cache_exists(fake_jira: JiraClient):
    assert str(fake_jira.cache.root) != ".jira_cache_test"
    list_of = [str(_).split('/')[-1] for _ in fake_jira.cache.root.iterdir()]
    assert len(list(fake_jira.cache.root.iterdir())) == 2, f'Iter root expected two values, got: {list_of}'
    for item in fake_jira.cache.root.iterdir():
        assert item.name in ("system", "issues")
    assert len(list(fake_jira.cache.system.iterdir())) == 2
    for item in fake_jira.cache.system.iterdir():
        assert item.name in ("createmeta", "editmeta")


json_response_account = {
    "accountId": "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz",
    "emailAddress": "user@domain.com",
    "displayName": "Marcus Aurelius",
}


def test_get_current_user(fake_jira: JiraClient, requests_mock):
    api_url = fake_jira.options.url + "/rest/api/latest"
    requests_mock.get(f'{api_url}/myself', json=json_response_account)
    assert fake_jira.get_current_user() == {
        "accountId": "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz",
        "emailAddress": "user@domain.com",
        "displayName": "Marcus Aurelius",
    }


def test_get_current_user_account_id(fake_jira: JiraClient, requests_mock):
    api_url = fake_jira.options.url + "/rest/api/latest"
    requests_mock.get(f'{api_url}/myself', json=json_response_account)
    assert (
        fake_jira.get_current_user_account_id()
        == "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz"
    )


def test_get_current_user_as_assignee(fake_jira: JiraClient, requests_mock):
    api_url = fake_jira.options.url + "/rest/api/latest"
    requests_mock.get(f'{api_url}/myself', json=json_response_account)
    assert fake_jira.get_current_user_as_assignee() == {
        "assignee": {"accountId": "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz"}
    }


def test_get_test_auth_success(fake_jira: JiraClient, capsys, requests_mock):
    api_url = fake_jira.options.url + "/rest/api/latest"
    requests_mock.get(f'{api_url}/myself', json=json_response_account)
    assert fake_jira.test_auth()
    captured = capsys.readouterr()
    assert captured.out == "Connected as user: Marcus Aurelius\n"
    assert captured.err == ""


def test_get_test_auth_connection_error(fake_jira: JiraClient, capsys):
    with patch(
        "mantis.jira.jira_client.requests.get",
        side_effect=requests.exceptions.ConnectionError,
    ):
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            fake_jira.test_auth()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == (
        "Connection error. Run it like this:\n"
        "export JIRA_TOKEN=$(cat secret.txt)\n"
        "python main.py\n"
    )
    assert captured.err == ""


def test_get_test_auth_generic_exception(fake_jira: JiraClient, capsys):
    with patch(
        "mantis.jira.jira_client.requests.get",
        side_effect=requests.exceptions.RequestException,
    ):
        with pytest.raises(requests.exceptions.RequestException):
            fake_jira.test_auth()
    captured = capsys.readouterr()
    assert captured.out == ("test_auth failed for unknown reasons.\n")
    assert captured.err == ""
