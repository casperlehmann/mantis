import os

import pytest

from mantis.jira import JiraAuth, JiraClient


@pytest.fixture
def fake_jira_client_for_test_auth(opts_from_fake_cli, mock_get_request):
    mock_get_request.return_value.json.return_value = {}
    auth = JiraAuth(opts_from_fake_cli)
    return JiraClient(opts_from_fake_cli, auth)


@pytest.mark.skipif(
    not os.path.exists("options.toml"), reason='File "options.toml" does not exist'
)
@pytest.mark.skipif(
    not os.getenv("EXECUTE_SKIPPED"), reason="This is a live test against the Jira api"
)
def test_jira_options_override(fake_jira_client_for_test_auth):
    fake_jira_client_for_test_auth.test_auth()


def test_cache_exists(fake_jira):
    assert str(fake_jira.cache.root) != ".jira_cache_test"
    assert len(list(fake_jira.cache.root.iterdir())) == 2
    for item in fake_jira.cache.root.iterdir():
        assert item.name in ("system", "issues")
    assert len(list(fake_jira.cache.system.iterdir())) == 1
    for item in fake_jira.cache.system.iterdir():
        assert item.name in ("issue_type_fields")


@pytest.fixture
def json_response_account_id(mock_get_request):
    mock_get_request.return_value.json.return_value = {
        "accountId": "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz"
    }


def test_get_current_user(fake_jira, json_response_account_id):
    assert fake_jira.get_current_user() == {
        "accountId": "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz"
    }


def test_get_current_user_account_id(fake_jira, json_response_account_id):
    assert (
        fake_jira.get_current_user_account_id()
        == "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz"
    )


def test_get_current_user_as_assignee(fake_jira, json_response_account_id):
    assert fake_jira.get_current_user_as_assignee() == {
        "assignee": {"accountId": "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz"}
    }
