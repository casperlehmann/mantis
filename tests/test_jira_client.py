import pytest
import requests

from unittest.mock import patch

from mantis.mantis_client import MantisClient
from tests.data import CacheData


class TestJiraClient:
    def test_test_auth_complains_with_bad_input(self, requests_mock, fake_mantis: MantisClient, capsys):
        requests_mock.get(f'{fake_mantis.http.api_url}/myself', json={})
        fake_mantis.jira.test_auth()
        captured = capsys.readouterr()
        assert captured.out == ("Connected as user: ERROR: No displayName\n")
        assert captured.err == ""

    def test_test_auth_informs_login(self, requests_mock, fake_mantis: MantisClient, capsys):
        requests_mock.get(f'{fake_mantis.http.api_url}/myself', json={'displayName': 'Buddy'})
        fake_mantis.jira.test_auth()
        captured = capsys.readouterr()
        assert captured.out == ("Connected as user: Buddy\n")
        assert captured.err == ""

    def test_cache_exists(self, fake_mantis: MantisClient):
        assert str(fake_mantis.cache.root) != ".jira_cache_test"
        list_of = [str(_).split('/')[-1] for _ in fake_mantis.cache.root.iterdir()]
        assert len(list(fake_mantis.cache.root.iterdir())) == 2, f'Iter root expected two values, got: {list_of}'
        assert {item.name for item in fake_mantis.cache.root.iterdir()} == {"system", "issues"}
        assert len(list(fake_mantis.cache.system.iterdir())) == 4
        assert {item.name for item in fake_mantis.cache.system.iterdir()} == {"createmeta", 'createmeta_schemas', "editmeta", 'editmeta_schemas'}

    def test_get_current_user(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/myself', json=CacheData().placeholder_account)
        assert fake_mantis.jira.get_current_user() == {
            "accountId": "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz",
            "emailAddress": "marcus@rome.gov",
            "displayName": "Marcus Aurelius",
        }

    def test_get_current_user_account_id(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/myself', json=CacheData().placeholder_account)
        assert (
            fake_mantis.jira.get_current_user_account_id()
            == "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz"
        )

    def test_get_current_user_as_assignee(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/myself', json=CacheData().placeholder_account)
        assert fake_mantis.jira.get_current_user_as_assignee() == {
            "assignee": {"accountId": "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz"}
        }

    def test_get_test_auth_success(self, fake_mantis: MantisClient, capsys, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/myself', json=CacheData().placeholder_account)
        assert fake_mantis.jira.test_auth()
        captured = capsys.readouterr()
        assert captured.out == "Connected as user: Marcus Aurelius\n"
        assert captured.err == ""

    def test_get_test_auth_connection_error(self, fake_mantis: MantisClient, capsys):
        with patch(
            "jira.jira_client.requests.get",
            side_effect=requests.exceptions.ConnectionError,
        ):
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                fake_mantis.jira.test_auth()
            assert pytest_wrapped_e.type is SystemExit
            assert pytest_wrapped_e.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == (
            "Connection error. Run it like this:\n"
            "export JIRA_TOKEN=$(cat secret.txt)\n"
            "uv run python main.py\n"
        )
        assert captured.err == ""

    def test_get_test_auth_generic_exception(self, fake_mantis: MantisClient, capsys):
        with patch(
            "jira.jira_client.requests.get",
            side_effect=requests.exceptions.RequestException,
        ):
            with pytest.raises(requests.exceptions.RequestException):
                fake_mantis.jira.test_auth()
        captured = capsys.readouterr()
        assert captured.out == ("test_auth failed for unknown reasons.\n")
        assert captured.err == ""

    def test_jql_auto_complete_returns_json(self, fake_mantis: MantisClient, requests_mock):
        url = f'{fake_mantis.http.api_url}/jql/autocompletedata/suggestions?fieldName=reporter&fieldValue=Marcus'
        accountId = CacheData().placeholder_account['accountId']
        return_value = {'results': [{'value': accountId, 'displayName': '<b>Marcus</b> Aurelius - <b>marcus</b>@rome.gov'}]}
        requests_mock.get(url, json=return_value)
        raw_auto_complete = fake_mantis.jira.jql_auto_complete('reporter', 'Marcus')
        assert raw_auto_complete == return_value

    def test_validate_input_returns_one_suggestion(self, fake_mantis: MantisClient, requests_mock, capsys):
        url = f'{fake_mantis.http.api_url}/jql/autocompletedata/suggestions?fieldName=cf[10001]&fieldValue=Commerce'
        entry = {'value': 'abc123', 'displayName': 'E-<b>Commerce</b> Checkout Team'}
        return_value = {'results': [entry]}
        requests_mock.get(url, json=return_value)
        validation_suggestions = fake_mantis.jira.validate_input('cf[10001]', 'Commerce')
        assert validation_suggestions[0].display_name == 'E-Commerce Checkout Team'
        captured = capsys.readouterr()
        assert captured.out == ('Single match found for cf[10001] "Commerce":\n- E-Commerce Checkout Team (abc123)\n')
        assert captured.err == ""

    def test_validate_input_returns_multiple_suggestion(self, fake_mantis: MantisClient, requests_mock, capsys):
        url = f'{fake_mantis.http.api_url}/jql/autocompletedata/suggestions?fieldName=cf[10001]&fieldValue=Commerce'
        entry_1 = {'value': 'abc123', 'displayName': 'E-<b>Commerce</b> Checkout Team'}
        entry_2 = {'value': 'abc124', 'displayName': 'E-<b>Commerce</b> Checkin Team'}
        return_value = {'results': [entry_1, entry_2]}
        requests_mock.get(url, json=return_value)
        validation_suggestions = fake_mantis.jira.validate_input('cf[10001]', 'Commerce')
        assert validation_suggestions[0].display_name == 'E-Commerce Checkout Team'
        assert validation_suggestions[1].display_name == 'E-Commerce Checkin Team'
        captured = capsys.readouterr()
        assert captured.out == (
            'Ambiguous result:\n'
            '- E-Commerce Checkout Team (abc123)\n'
            '- E-Commerce Checkin Team (abc124)\n')
        assert captured.err == ""

    def test_validate_input_returns_no_suggestions(self, fake_mantis: MantisClient, requests_mock, capsys):
        url = f'{fake_mantis.http.api_url}/jql/autocompletedata/suggestions?fieldName=cf[10001]&fieldValue=Freeloader'
        return_value: dict[str, list[dict]] = {'results': []}
        requests_mock.get(url, json=return_value)
        validation_suggestions = fake_mantis.jira.validate_input('cf[10001]', 'Freeloader')
        assert len(validation_suggestions) == 0
        captured = capsys.readouterr()
        assert captured.out == 'No results found for cf[10001] "Freeloader"\n'
        assert captured.err == ""

    def test_get_field_names(self, fake_mantis: MantisClient, requests_mock):
        return_value = CacheData().get_names
        url = f'{fake_mantis.http.api_url}/issue/ECS-2?expand=names'
        requests_mock.get(url, json=return_value)
        fetch_field_names = fake_mantis.jira.get_field_names('ECS-2')
        assert isinstance(fetch_field_names, dict)
        assert set(fetch_field_names.keys()) == {'id', 'expand', 'self', 'names', 'key', 'fields'}
        assert fetch_field_names['names'].get('aggregateprogress') == 'Σ Progress'
        assert fetch_field_names['names'].get('customfield_10035') == 'Design'
