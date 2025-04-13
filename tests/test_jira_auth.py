import pytest

from jira import JiraOptions
from jira import JiraAuth

from requests.auth import HTTPBasicAuth

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jira.jira_options import JiraOptions

def test_CreatesJiraAuthSettings(fake_toml):
    opts = JiraOptions(toml_source = fake_toml)
    auth = JiraAuth(opts)
    assert isinstance(auth.auth, HTTPBasicAuth)

def test_FailedJiraAuthSettingsRaises(fake_cli):
    fake_cli.personal_access_token = None
    with pytest.raises(PermissionError):
        JiraAuth(fake_cli).auth
