import pytest
from unittest.mock import patch

from dataclasses import dataclass
import requests

from mantis.jira import JiraOptions, JiraAuth, JiraClient, JiraIssues

@dataclass
class Cli:
    user = 'user_1@domain.com'
    url = 'https://account_1.atlassian-host.net'
    personal_access_token = 'SECRET_1'
    project = 'TEST'
    no_verify_ssl = False
    cache_dir = ".jira_cache_test"
    drafts_dir = "drafts_test"
    action = ''
    issues = ['']

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
        'project = "TEST"',
        'cache-dir = ".jira_cache_test"',
        'drafts-dir = "drafts_test"'
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
    return JiraClient(opts_from_user_toml, auth)

@pytest.fixture
def jira_client_from_fake_cli(opts_from_fake_cli):
    auth = JiraAuth(opts_from_fake_cli)
    return JiraClient(opts_from_fake_cli, auth)

@pytest.fixture
def jira_issues_from_fake_cli(jira_client_from_fake_cli):
    return JiraIssues(jira_client_from_fake_cli)

