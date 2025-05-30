from typing import TYPE_CHECKING

import pytest
from requests.auth import HTTPBasicAuth

from mantis.jira import JiraAuth, JiraOptions

if TYPE_CHECKING:
    from mantis.jira.jira_options import JiraOptions


class TestJiraAuth:
    def test_creates_jira_auth_settings(self, fake_toml):
        opts = JiraOptions(toml_source=fake_toml)
        auth = JiraAuth(opts)
        assert isinstance(auth.auth, HTTPBasicAuth)

    def test_failed_jira_auth_settings_raises(self, fake_cli):
        fake_cli.personal_access_token = None
        with pytest.raises(PermissionError):
            JiraAuth(fake_cli).auth
