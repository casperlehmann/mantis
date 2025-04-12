import pytest
from dataclasses import dataclass

from jira import JiraOptions

OPTIONS_CONTENT = '''
[jira]
user = "user@domain.com"
url = "https://account.atlassian.net"
personal-access-token = "zxcv_JIRA_TOKEN"
'''

def test_JiraOptions(tmpdir):
    toml = tmpdir / "options.toml"
    toml.write(OPTIONS_CONTENT)
    opts = JiraOptions(toml_source = toml)
    assert opts.user == 'user@domain.com'
    assert opts.url == 'https://account.atlassian.net'
    assert opts.personal_access_token == 'zxcv_JIRA_TOKEN'

def test_JiraOptionsOverride(tmpdir):
    toml = tmpdir / "options.toml"
    toml.write(OPTIONS_CONTENT)
    @dataclass
    class cli:
        user = 'admin@domain.com'
        jira_url = 'https://admin.atlassian.net'
        personal_access_token = 'SECRET'
    opts = JiraOptions(toml_source = toml, parser = cli())
    assert opts.user == 'admin@domain.com'
    assert opts.url == 'https://admin.atlassian.net'
    assert opts.personal_access_token == 'SECRET'

def test_JiraOptionsNotSet(tmpdir):
    toml = tmpdir / "options.toml"
    with pytest.raises(FileNotFoundError) as e:
        opts = JiraOptions(toml_source = toml)
    toml.write('')
    with pytest.raises(AssertionError) as e:
        opts = JiraOptions(toml_source = toml)
