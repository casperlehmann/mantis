import pytest

from jira import JiraOptions

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

def test_opts_from_user_toml_values(opts_from_user_toml):
    assert opts_from_user_toml.user != 'admin@domain.com'
    assert opts_from_user_toml.url != 'https://admin.atlassian.net'
    assert opts_from_user_toml.personal_access_token != 'SECRET'
