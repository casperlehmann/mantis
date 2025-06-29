import pytest
from requests.auth import HTTPBasicAuth

from mantis.jira import JiraAuth
from mantis.options_loader import OptionsLoader


class TestJiraAuth:
    def test_creates_jira_auth_settings(self):
        opts = OptionsLoader()
        auth = JiraAuth(opts)
        assert isinstance(auth.auth, HTTPBasicAuth)

    def test_failed_jira_auth_settings_raises(self, fake_cli):
        fake_cli.personal_access_token = None
        with pytest.raises(PermissionError):
            JiraAuth(fake_cli).auth
