import pytest
from unittest.mock import patch

from dataclasses import dataclass
import requests

from jira import JiraOptions, JiraAuth, JiraClient

@dataclass
class Cli:
    user = 'user_1@domain.com'
    url = 'https://account_1.atlassian-host.net'
    personal_access_token = 'SECRET_1'
    no_verify_ssl = False

@pytest.fixture
def mock_post_request():
    with patch('requests.post') as mock_post:
        yield mock_post

@pytest.fixture
def mock_get_request():
    with patch('requests.get') as mock_get:
        yield mock_get

@pytest.fixture
def fake_toml(tmpdir):
    toml_contents = '\n'.join((
        '[jira]',
        'user = "user_2@domain.com"',
        'url = "https://account_2.atlassian-host.net"',
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
