import os

import pytest

from mantis.jira import JiraOptions
from mantis.jira.jira_options import parse_args


class TestJiraOptions:
    def test_jira_options(self, fake_toml):
        opts = JiraOptions(toml_source=fake_toml)
        assert opts.user == "user_2@domain.com"
        assert opts.url == "https://account_2.atlassian-host.net"
        assert opts.personal_access_token == "SECRET_2"
        assert opts.chat_gpt_base_url == 'https://api.fakeai.com/v1'


    def test_jira_options_override(self, fake_toml, fake_cli):
        opts = JiraOptions(toml_source=fake_toml, parser=fake_cli)
        assert opts.user == "user_1@domain.com"
        assert opts.url == "https://account_1.atlassian-host.net"
        assert opts.personal_access_token == "SECRET_1"


    def test_jira_options_not_set(self, tmpdir, capfd):
        toml = tmpdir / "options.toml"
        with pytest.raises(AssertionError):
            JiraOptions(toml_source=toml)
        out, _ = capfd.readouterr()
        assert out == 'No toml_source provided and default "options.toml" does not exist\n'
        toml.write("")
        with pytest.raises(AssertionError) as execution_error:
            JiraOptions(toml_source=toml)
        out, err = capfd.readouterr()
        assert out == ""
        assert err == ""
        assert str(execution_error.value) == "JiraOptions.user not set"

    def test_parse_args_issues(self):
        # We need to pass an empty list. If we didn't, pytest would default
        # to using sys.argv, which might contain '--cov-report html --cov'
        namespace = parse_args(['get-issue'])
        assert namespace.issues == []
        namespace = parse_args(['get-issue', "TEST-1", "TEST-2"])
        assert namespace.issues == ["TEST-1", "TEST-2"]

    @pytest.mark.parametrize(
        "attr_name,flag,value,unset",
        [
            ("user", "--user", "me", None),
            ("personal_access_token", "--personal-access-token", "super-secret", None),
            ("url", "--jira-url", "https://jira", None),
            ("project", "--jira-project", "PROJ", None),
            ("no_verify_ssl", "--no-verify-ssl", True, False),
            ("cache_dir", "--cache-dir", "cache", None),
            ("drafts_dir", "--drafts-dir", "drafts", None),
            ("plugins_dir", "--plugins-dir", "plugins", None),
            ("type_id_cutoff", "--type-id-cutoff", "", None),
        ]
    )
    def test_parse_arg_flags(self, attr_name, flag, value, unset):
        namespace = parse_args(['get-tasks'])
        assert getattr(namespace, attr_name) == unset
        # Cast to str to allow expecting None, True, False
        namespace = parse_args([flag, str(value), 'get-tasks'])
        assert getattr(namespace, attr_name) == value
