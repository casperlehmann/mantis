import os

import pytest

from mantis.jira import JiraOptions


def test_jira_options(fake_toml):
    opts = JiraOptions(toml_source=fake_toml)
    assert opts.user == "user_2@domain.com"
    assert opts.url == "https://account_2.atlassian-host.net"
    assert opts.personal_access_token == "SECRET_2"


def test_jira_options_override(fake_toml, fake_cli):
    opts = JiraOptions(toml_source=fake_toml, parser=fake_cli)
    assert opts.user == "user_1@domain.com"
    assert opts.url == "https://account_1.atlassian-host.net"
    assert opts.personal_access_token == "SECRET_1"


def test_jira_options_not_set(tmpdir, capfd):
    toml = tmpdir / "options.toml"
    with pytest.raises(AssertionError):
        opts = JiraOptions(toml_source=toml)
    out, _ = capfd.readouterr()
    assert out == 'No toml_source provided and default "options.toml" does not exist\n'
    toml.write("")
    with pytest.raises(AssertionError):
        opts = JiraOptions(toml_source=toml)
        out, _ = capfd.readouterr()
    assert out == 'No toml_source provided and default "options.toml" does not exist\n'


@pytest.mark.skipif(
    not os.path.exists("options.toml"), reason='File "options.toml" does not exist'
)
def test_opts_from_user_toml_values(opts_from_user_toml):
    assert opts_from_user_toml.user != "user_1@domain.com"
    assert opts_from_user_toml.url != "https://account_1.atlassian-host.net"
    assert opts_from_user_toml.personal_access_token != "SECRET_1"
