import pytest
from dataclasses import dataclass

from jira import JiraOptions

@pytest.fixture
def fake_toml(tmpdir):
    toml_contents = '\n'.join((
        '[jira]',
        'user = "user@domain.com"',
        'url = "https://account.atlassian.net"',
        'personal-access-token = "zxcv_JIRA_TOKEN"',
        ''
    ))
    toml = tmpdir / "options.toml"
    toml.write(toml_contents)
    return toml

@dataclass
class Cli:
    user = 'admin@domain.com'
    jira_url = 'https://admin.atlassian.net'
    personal_access_token = 'SECRET'
    no_verify_ssl = False

@pytest.fixture
def fake_cli():
    return Cli()

def test_JiraOptions(fake_toml):
    opts = JiraOptions(toml_source = fake_toml)
    assert opts.user == 'user@domain.com'
    assert opts.url == 'https://account.atlassian.net'
    assert opts.personal_access_token == 'zxcv_JIRA_TOKEN'

def test_JiraOptionsOverride(fake_toml, fake_cli):
    opts = JiraOptions(toml_source = fake_toml, parser = fake_cli)
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
