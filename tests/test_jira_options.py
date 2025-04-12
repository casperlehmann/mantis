import pytest

from jira import JiraOptions

def test_JiraOptions(fake_toml):
    opts = JiraOptions(toml_source = fake_toml)
    assert opts.user == 'user_2@domain.com'
    assert opts.url == 'https://account_2.atlassian.net'
    assert opts.personal_access_token == 'SECRET_2'

def test_JiraOptionsOverride(fake_toml, fake_cli):
    opts = JiraOptions(toml_source = fake_toml, parser = fake_cli)
    assert opts.user == 'user_1@domain.com'
    assert opts.url == 'https://account_1.atlassian.net'
    assert opts.personal_access_token == 'SECRET_1'

def test_JiraOptionsNotSet(tmpdir):
    toml = tmpdir / "options.toml"
    with pytest.raises(FileNotFoundError) as e:
        opts = JiraOptions(toml_source = toml)
    toml.write('')
    with pytest.raises(AssertionError) as e:
        opts = JiraOptions(toml_source = toml)

def test_OptsFromUserTomlValues(opts_from_user_toml):
    assert opts_from_user_toml.user != 'user_1@domain.com'
    assert opts_from_user_toml.url != 'https://account_1.atlassian.net'
    assert opts_from_user_toml.personal_access_token != 'SECRET_1'
