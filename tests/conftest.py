from dataclasses import dataclass
from pathlib import Path

import pytest

from mantis.jira import JiraClient
from mantis.mantis_client import MantisClient
from mantis.options_loader import OptionsLoader


@dataclass
class Cli:
    user = "user_1@domain.com"
    url = "https://account_1.atlassian-host.net"
    personal_access_token = "SECRET_1"
    project = "TEST"
    no_verify_ssl = False
    cache_dir = ".jira_cache_test"
    drafts_dir = "drafts_test"
    plugins_dir = "plugins_test"
    type_id_cutoff = "10100"
    action = ""
    issues = [""]
    chat_gpt_activated = False
    chat_gpt_base_url = "https://api.fakeai.com/v1"
    chat_gpt_api_key = "socks_off_full_throttle_$%^"


@pytest.fixture
def fake_toml(tmpdir):
    toml_contents = "\n".join(
        (
            "[jira]",
            'user = "user_2@domain.com"',
            'url = "https://account_2.atlassian-host.net"',
            'personal-access-token = "SECRET_2"',
            'project = "TEST"',
            'cache-dir = ".jira_cache_test"',
            'drafts-dir = "drafts_test"',
            'plugins-dir = "plugins_test"',
            'type-id-cutoff = "10100"',
            "",
            '[openai]',
            'chat-gpt-activated = false',
            'chat-gpt-base-url = "https://api.fakeai.com/v1"',
            'chat-gpt-api-key = "socks_off_full_throttle_$%^"',
            "",
        )
    )
    toml = tmpdir / "options.toml"
    toml.write(toml_contents)
    return toml


@pytest.fixture
def fake_cli():
    return Cli()


@pytest.fixture
def opts_from_fake_cli(fake_cli):
    return OptionsLoader(parser=fake_cli)


@pytest.fixture
def jira_client_from_fake_cli(opts_from_fake_cli):
    mantis = MantisClient(opts_from_fake_cli)
    return mantis.jira


@pytest.fixture
def with_no_read_cache(fake_jira: JiraClient):
    fake_jira.mantis._no_read_cache = True


@pytest.fixture
def with_fake_cache(opts_from_fake_cli, tmp_path: Path):
    (tmp_path / "cache").mkdir(exist_ok=True)
    opts_from_fake_cli.cache_dir = tmp_path / "cache"


@pytest.fixture
def with_fake_drafts_dir(opts_from_fake_cli, tmp_path: Path):
    (tmp_path / "drafts").mkdir(exist_ok=True)
    opts_from_fake_cli.drafts_dir = tmp_path / "drafts"


@pytest.fixture
def with_fake_plugins_dir(opts_from_fake_cli, tmp_path: Path):
    (tmp_path / "plugins").mkdir(exist_ok=True)
    opts_from_fake_cli.plugins_dir = tmp_path / "plugins"


@pytest.fixture
def minimal_issue_payload():
    return {
        "key": "TASK-1",
        "fields": {
            "summary": "redacted",
            "header": "redacted",
            "project": {"key": "redacted", "name": "redacted"},
            "parent": "redacted",
            "issuetype": {"id": "10001", "name": "Task"},
            "assignee": "redacted",
            "key": "redacted",
            "reporter": "redacted",
            "status": {"name": "resolved"},
            "description": "redacted"
        }
    }

@pytest.fixture
def fake_jira(
    with_fake_cache,
    with_fake_drafts_dir,
    with_fake_plugins_dir,
    jira_client_from_fake_cli,
    minimal_issue_payload,
):
    jira = jira_client_from_fake_cli
    assert str(jira.mantis.cache.root) != ".jira_cache_test"
    assert str(jira.mantis.drafts_dir) != "drafts_test"
    assert str(jira.mantis.plugins_dir) != "plugins_test"
    return jira
