from dataclasses import dataclass
from pathlib import Path

import pytest
from unittest.mock import patch

from mantis.mantis_client import MantisClient
from mantis.options_loader import OptionsLoader


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
    toml = tmpdir / "mantis.toml"
    toml.write(toml_contents)
    return toml


@pytest.fixture
def patch_load_toml(tmpdir, fake_toml):
    """
    Patch OptionsLoader.load_toml so that it always reads the TOML file under tmpdir,
    regardless of the toml_path parameter passed.
    """
    import tomllib
    def _load_toml_patch(self, toml_path=None):
        path = tmpdir / "mantis.toml"
        with open(path, "rb") as f:
            return tomllib.load(f)
    with patch('mantis.options_loader.OptionsLoader.load_toml', new=_load_toml_patch):
        yield


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
def fake_cli():
    """Create a fake CLI object with default values for testing option overrides"""
    return Cli()


@pytest.fixture
def opts_from_fake_cli(fake_cli):
    return OptionsLoader(parser=fake_cli)


@pytest.fixture
def with_no_read_cache(fake_mantis: MantisClient):
    fake_mantis._no_read_cache = True


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

# The execution order is determined by the fixture dependency graph, not by the order in the file or the order in the function signature. Pytest always sets up dependencies first, from the leaves up to the fixture requested by the test.
@pytest.fixture
def fake_mantis(
    with_fake_cache,
    with_fake_drafts_dir,
    with_fake_plugins_dir,
    patch_load_toml,
    opts_from_fake_cli,
    minimal_issue_payload,
):
    mantis = MantisClient(opts_from_fake_cli)
    assert str(mantis.jira.mantis.cache.root) != ".jira_cache_test"
    assert str(mantis.jira.mantis.drafts_dir) != "drafts_test"
    assert str(mantis.jira.mantis.plugins_dir) != "plugins_test"
    return mantis
