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
