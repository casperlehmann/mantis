import pytest

from jira import JiraOptions
from jira import JiraAuth

from requests.auth import HTTPBasicAuth
from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jira.jira_options import JiraOptions

OPTIONS_CONTENT = '''
[jira]
user = "user@domain.com"
url = "https://account.atlassian.net"
personal-access-token = "zxcv_JIRA_TOKEN"
'''

def test_CreatesJiraAuthSettings(tmpdir):
    toml = tmpdir / "options.toml"
    toml.write(OPTIONS_CONTENT)
    opts = JiraOptions(toml_source = toml)
    auth = JiraAuth(opts)
    assert opts.user == 'user@domain.com'
    assert opts.url == 'https://account.atlassian.net'
    assert opts.personal_access_token == 'zxcv_JIRA_TOKEN'
    assert isinstance(auth.auth, HTTPBasicAuth)

def test_FailedJiraAuthSettingsRaises(tmpdir):
    @dataclass
    class OptsMock:
        personal_access_token = None
        url = 'exists'
    opts = OptsMock()
    with pytest.raises(PermissionError) as e:
        JiraAuth(opts).auth
