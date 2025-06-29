import os

import pytest

from mantis.options_loader import OptionsLoader, parse_args


class TestJiraOptions:
    def test_options(self, patch_load_toml):
        opts = OptionsLoader()
        assert opts.user == "user_2@domain.com"
        assert opts.url == "https://account_2.atlassian-host.net"
        assert opts.personal_access_token == "SECRET_2"
        assert opts.chat_gpt_base_url == 'https://api.fakeai.com/v1'


    def test_options_override(self, fake_cli):
        opts = OptionsLoader(parser=fake_cli)
        assert opts.user == "user_1@domain.com"
        assert opts.url == "https://account_1.atlassian-host.net"
        assert opts.personal_access_token == "SECRET_1"


    def test_options_not_set(self, tmpdir, patch_load_toml, capfd):
        toml = tmpdir / "mantis.toml"
        toml.write("")
        with pytest.raises(AssertionError) as execution_error:
            OptionsLoader()
        assert str(execution_error.value) == "OptionsLoader.user not set"
        out, err = capfd.readouterr()
        assert out == ""
        assert err == ""

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
