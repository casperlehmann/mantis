import pytest
from dataclasses import dataclass
import os
from jira import JiraOptions, JiraAuth, JiraClient

from .conftest import RequestsMock, RequestsResultMock

@pytest.fixture
def fake_jira_client_for_test_auth(opts_from_fake_cli):
    request_mock = RequestsMock(get_return = {})
    auth = JiraAuth(opts_from_fake_cli)
    return JiraClient(opts_from_fake_cli, auth, request_mock)

@pytest.mark.skipif(not os.path.exists("options.toml"), reason='File "options.toml" does not exist')
def test_JiraOptionsOverride(fake_toml, fake_jira_client_for_test_auth):
    fake_jira_client_for_test_auth.test_auth()
