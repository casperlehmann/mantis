import argparse
import tomllib


class JiraOptions:
    """Collects options from toml file, allowing for command line overrides

    python jira/jira_options.py --user user@domain.com --personal-access-token $JIRA_TOKEN --jira-url=https://account.atlassian.net
    """

    default_toml_source = "options.toml"

    def __init__(
        self,
        parser: "argparse.Namespace | None" = None,
        toml_source: str | None = None,
    ):
        if not toml_source:
            toml_source = self.default_toml_source
        try:
            with open(toml_source, "rb") as f:
                options = tomllib.load(f)
        except FileNotFoundError:
            print('No toml_source provided and default "options.toml" does not exist')
            toml_source = None
            options = {}
        self.user = parser and parser.user or options.get("jira", {}).get("user")
        self.personal_access_token = (
            parser
            and parser.personal_access_token
            or options.get("jira", {}).get("personal-access-token")
        )
        self.url = parser and parser.url or options.get("jira", {}).get("url")
        self.project = (
            parser and parser.project or options.get("jira", {}).get("project")
        )
        self.no_verify_ssl = bool(
            parser
            and parser.no_verify_ssl
            or options.get("jira", {}).get("no-verify-ssl")
        )
        self.cache_dir = (
            parser and parser.cache_dir or options.get("jira", {}).get("cache-dir")
        )
        self.drafts_dir = (
            parser and parser.drafts_dir or options.get("jira", {}).get("drafts-dir")
        )
        self.plugins_dir = (
            parser and parser.plugins_dir or options.get("jira", {}).get("plugins-dir")
        )
        self.type_id_cutoff = int(
            parser
            and parser.type_id_cutoff
            or options.get("jira", {}).get("type-id-cutoff", 10100)
        )
        self.action = parser and parser.action or ""
        self.issues: list[str] = parser and parser.issues or []
        assert self.user, "JiraOptions.user not set"
        assert self.personal_access_token, "JiraOptions.personal_access_token not set"
        assert self.url, "JiraOptions.url not set"
        assert self.project, "JiraOptions.project not set"
        assert self.cache_dir, "JiraOptions.cache_dir not set"
        assert self.drafts_dir, "JiraOptions.drafts_dir not set"
        assert self.plugins_dir, "JiraOptions.plugins_dir not set"


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
        "--action", dest="action", default="get-issue", help="Get an issue from Jira"
    )
    parser.add_argument(
        "issues",
        nargs="*",
        help="List of issues by key (e.g. TASK-1, TASK-2, TASK-3, etc.)",
    )
    return parser.parse_args(args_overwrite)
