import pytest
import os
import requests
from mantis.jira import JiraAuth, JiraClient

@pytest.fixture
def fake_jira_client_for_test_auth(opts_from_fake_cli, mock_get_request):
    mock_get_request.return_value.json.return_value = {}
    auth = JiraAuth(opts_from_fake_cli)
    return JiraClient(opts_from_fake_cli, auth)

@pytest.mark.skipif(not os.path.exists("options.toml"), reason='File "options.toml" does not exist')
def test_jira_options_override(fake_jira_client_for_test_auth):
    fake_jira_client_for_test_auth.test_auth()

