import pytest
from dataclasses import dataclass
import requests

from jira import JiraOptions, JiraAuth, JiraClient

from dataclasses import dataclass

@dataclass
class Cli:
    user = 'user_1@domain.com'
    url = 'https://account_1.atlassian.net'
    personal_access_token = 'SECRET_1'
    no_verify_ssl = False

class RequestsResultMock:
    def __init__(self, get_return):
        self._get_return = get_return

    def get(self):
        return self
    
    def raise_for_status(self):
        return self

    def json(self):
        return self._get_return

class RequestsMock:
    def __init__(self, get_return):
        self._get_return = get_return

    def get(self, *args, **kwargs):
        return RequestsResultMock(self._get_return)

@pytest.fixture
def fake_toml(tmpdir):
    toml_contents = '\n'.join((
        '[jira]',
        'user = "user_2@domain.com"',
        'url = "https://account_2.atlassian.net"',
        'personal-access-token = "SECRET_2"',
        ''
    ))
    toml = tmpdir / "options.toml"
    toml.write(toml_contents)
    return toml

@pytest.fixture
def fake_cli():
    return Cli()

@pytest.fixture
def opts_from_fake_cli(fake_cli):
    return JiraOptions(parser = fake_cli)

@pytest.fixture
def opts_from_user_toml():
    return JiraOptions()

@pytest.fixture
def jira_client_from_user_toml(opts_from_user_toml):
    auth = JiraAuth(opts_from_user_toml)
    return JiraClient(opts_from_user_toml, auth, requests)
