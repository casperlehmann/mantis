import argparse
from pathlib import Path
import tomllib

from xdg_base_dirs import xdg_config_home


MANTIS_TOML = "mantis.toml"


class OptionsLoader:
    """Collects options from toml file, allowing for command line overrides"""
    def __init__(self, parser: "argparse.Namespace | None" = None) -> None:
        self.options = {}
        self.options.update(self.default_toml())
        self.options.update(self.cwd_toml())
        self.parser = parser
        self.sanity_check()

    def load_toml(self, toml_path: Path) -> dict:
        """Load options from a TOML file."""
        if not toml_path.is_file():
            return {}
        with open(toml_path, "rb") as f:
            return tomllib.load(f)

    def default_toml(self) -> dict:
        """Get the mantis directory under either XDG config home or user home"""
        config_home = xdg_config_home()
        return self.load_toml(config_home / MANTIS_TOML)

    def cwd_toml(self) -> dict:
        """Get the mantis directory under either XDG config home or user home"""
        return self.load_toml(Path.cwd() / MANTIS_TOML)

    def sanity_check(self) -> None:
        """Check that all required options are set."""
        assert self.user, "OptionsLoader.user not set"
        assert self.personal_access_token, "OptionsLoader.personal_access_token not set"
        assert self.url, "OptionsLoader.url not set"
        assert self.project, "OptionsLoader.project not set"
        assert self.cache_dir, "OptionsLoader.cache_dir not set"
        assert self.drafts_dir, "OptionsLoader.drafts_dir not set"
        assert self.plugins_dir, "OptionsLoader.plugins_dir not set"
        if self.chat_gpt_activated:
            assert self.chat_gpt_base_url, f"ChatGPT is activated, but OptionsLoader.chat_gpt_base_url not set {self.options}"
            assert self.chat_gpt_api_key, f"ChatGPT is activated, but OptionsLoader.chat_gpt_api_key not set {self.options}"

    @property
    def user(self) -> str:
        val = self.parser and self.parser.user or self.options.get("jira", {}).get("user")
        assert val, "OptionsLoader.user not set"
        return val

    @property
    def personal_access_token(self) -> str | None:
        return (
            self.parser
            and self.parser.personal_access_token
            or self.options.get("jira", {}).get("personal-access-token")
        )

    @property
    def url(self) -> str | None:
        return self.parser and self.parser.url or self.options.get("jira", {}).get("url")

    @property
    def project(self) -> str:
        val = self.parser and self.parser.project or self.options.get("jira", {}).get("project")
        assert val, "OptionsLoader.project not set"
        return val

    @property
    def no_verify_ssl(self) -> bool:
        return bool(
            self.parser
            and self.parser.no_verify_ssl
            or self.options.get("jira", {}).get("no-verify-ssl")
        )

    @property
    def cache_dir(self) -> str:
        val = self.parser and self.parser.cache_dir or self.options.get("jira", {}).get("cache-dir")
        assert val, "OptionsLoader.cache_dir not set"
        return val
        
    @cache_dir.setter
    def cache_dir(self, value: str) -> None:
        if self.parser:
            self.parser.cache_dir = value
        else:
            self.options["jira"]["cache-dir"] = value

    @property
    def drafts_dir(self) -> str:
        val = self.parser and self.parser.drafts_dir or self.options.get("jira", {}).get("drafts-dir")
        assert val, "OptionsLoader.drafts_dir not set"
        return val

    @drafts_dir.setter
    def drafts_dir(self, value: str) -> None:
        if self.parser:
            self.parser.drafts_dir = value
        else:
            self.options["jira"]["drafts-dir"] = value

    @property
    def plugins_dir(self) -> str:
        val = self.parser and self.parser.plugins_dir or self.options.get("jira", {}).get("plugins-dir")
        assert val, "OptionsLoader.plugins_dir not set"
        return val

    @plugins_dir.setter
    def plugins_dir(self, value: str) -> None:
        if self.parser:
            self.parser.plugins_dir = value
        else:
            self.options["jira"]["plugins-dir"] = value

    @property
    def type_id_cutoff(self) -> int:
        return int(
            self.parser
            and self.parser.type_id_cutoff
            or self.options.get("jira", {}).get("type-id-cutoff", 10100)
        )


    @property
    def chat_gpt_base_url(self) -> str | None:
        return (
            self.parser
            and self.parser.chat_gpt_base_url
            or self.options.get("openai", {}).get("chat-gpt-base-url")
        )

    @property
    def chat_gpt_api_key(self) -> str | None:
        return (
            self.parser
            and self.parser.chat_gpt_api_key
            or self.options.get("openai", {}).get("chat-gpt-api-key")
        )

    @property
    def chat_gpt_activated(self) -> bool:
        return bool(
            # Since a bool can be False, we can't rely on the truthiness of the value and use "or" like in the other cases.
            self.parser.chat_gpt_activated if self.parser and isinstance(self.parser.chat_gpt_activated, bool)
            else self.options.get("openai", {}).get("chat-gpt-activated", False)
        )

    @property
    def action(self) -> str:
        return self.parser and self.parser.action or ""

    @property
    def issues(self) -> list[str]:
        return self.parser and self.parser.issues or []
    


def parse_args(args_overwrite: list[str] | None = None) -> argparse.Namespace:
    """Parse sys.argv (or optional list of strings) and return argparse Namespace"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--user", dest="user", default=None, help="Username to access JIRA"
    )
    parser.add_argument(
        "-t",
        "--personal-access-token",
        dest="personal_access_token",
        default=None,
        help="Personal Access Token from JIRA",
    )
    parser.add_argument(
        "-j",
        "--jira-url",
        dest="url",
        help="JIRA Tenant base URL (e.g. https://account.atlassian.net)",
    )
    parser.add_argument(
        "-p",
        "--jira-project",
        dest="project",
        help="JIRA project (i.e. the thing in front of the hyphen in your task key)",
    )
    parser.add_argument(
        "--no-verify-ssl",
        dest="no_verify_ssl",
        default=False,
        action="store_true",
        help="Do not verify SSL certificates for requests",
    )
    parser.add_argument(
        "--cache-dir",
        dest="cache_dir",
        default=None,
        help="Set the local cache for Jira data",
    )
    parser.add_argument(
        "--drafts-dir",
        dest="drafts_dir",
        default=None,
        help="Set the local drafts directory for Jira issues",
    )
    parser.add_argument(
        "--plugins-dir",
        dest="plugins_dir",
        default=None,
        help="Set the local plugins directory for models",
    )
    parser.add_argument(
        "--type-id-cutoff",
        dest="type_id_cutoff",
        default=None,
        help="Set the cutoff for Jira types to fetch",
    )
    parser.add_argument(
        "--chat-gpt-base-url",
        dest='chat_gpt_base_url',
        default=None,
        help="Base URL for the ChatGPT API",
    )
    parser.add_argument(
        "--chat-gpt-api-key",
        dest='chat_gpt_api_key',
        default=None,
        help="API Key for the ChatGPT API",
    )
    parser.add_argument(
        "--chat-gpt-activated",
        dest='chat_gpt_activated',
        default=None,
        help="Activation of ChatGPT API",
    )
    parser.add_argument(
        "action",
        help="Action to perform (e.g. get-issue, create-issue, etc.)",
    )
    parser.add_argument(
        "issues",
        nargs="*",
        help="List of issues by key (e.g. TASK-1, TASK-2, TASK-3, etc.)",
    )
    return parser.parse_args(args_overwrite)
