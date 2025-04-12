import pytest
from dataclasses import dataclass

from jira import JiraOptions

@pytest.fixture
def fake_toml():
    return '\n'.join((
        '[jira]',
        'user = "user@domain.com"',
        'url = "https://account.atlassian.net"',
        'personal-access-token = "zxcv_JIRA_TOKEN"',
        ''
    ))

def test_JiraOptions(tmpdir, fake_toml):
    toml = tmpdir / "options.toml"
    toml.write(fake_toml)
    opts = JiraOptions(toml_source = toml)
    assert opts.user == 'user@domain.com'
    assert opts.url == 'https://account.atlassian.net'
    assert opts.personal_access_token == 'zxcv_JIRA_TOKEN'

def test_JiraOptionsOverride(tmpdir, fake_toml):
    toml = tmpdir / "options.toml"
    toml.write(fake_toml)
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

def test_JiraOptionsNotSet(tmpdir):
    toml = tmpdir / "options.toml"
    with pytest.raises(FileNotFoundError) as e:
        opts = JiraOptions(toml_source = toml)
    toml.write('')
    with pytest.raises(AssertionError) as e:
        opts = JiraOptions(toml_source = toml)
