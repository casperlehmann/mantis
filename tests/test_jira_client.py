import pytest
from dataclasses import dataclass

class requestsMock:
    def get(self, *args, **kwargs):
        return self
    def raise_for_status(self):
        return {}
    def json(self):
        return {}

from jira import JiraOptions, JiraAuth, JiraClient, parse_args

OPTIONS_CONTENT = '''
[jira]
user = "user@domain.com"
url = "https://account.atlassian.net"
personal-access-token = "zxcv_JIRA_TOKEN"
'''

def test_JiraOptionsOverride(tmpdir):
    toml = tmpdir / "options.toml"
    toml.write(OPTIONS_CONTENT)
    @dataclass
    class cli:
        user = 'admin@domain.com'
        jira_url = 'https://admin.atlassian.net'
        personal_access_token = 'SECRET'
        no_verify_ssl = False
    opts = JiraOptions(toml_source = toml, parser = cli())
    assert opts.user == 'admin@domain.com'
    assert opts.url == 'https://admin.atlassian.net'
    assert opts.personal_access_token == 'SECRET'
    auth = JiraAuth(opts)
    jira = JiraClient(opts, auth, requestsMock())
    jira.test_auth()
