import argparse
import tomllib
from typing import Optional

class JiraOptions:
    """Collects options from toml file, allowing for command line overrides
    
    python jira/jira_options.py --user user@domain.com --personal-access-token $JIRA_TOKEN --jira-url=https://account.atlassian.net
    """
    default_toml_source = "options.toml"

    def __init__(self, parser: Optional['argparse.Namespace'] = None, toml_source: Optional[str] = None, ):
        if not toml_source:
            toml_source = self.default_toml_source
        try:
            with open(toml_source, "rb") as f:
                options = tomllib.load(f)
        except FileNotFoundError:
            print ('No toml_source provided and default "options.toml" does not exist')
            toml_source = None
            options = {}
        self.user = parser and parser.user or options.get('jira', {}).get('user')
        self.personal_access_token = parser and parser.personal_access_token or options.get('jira', {}).get('personal-access-token')
        self.url = parser and parser.url or options.get('jira', {}).get('url')
        self.no_verify_ssl = bool(parser and parser.no_verify_ssl or options.get('jira', {}).get('no-verify-ssl'))
        self.action = parser and parser.action or ''
        self.issues: list[str] = parser and parser.issues or []
        assert self.user, 'JiraOptions.user not set'
        assert self.personal_access_token, 'JiraOptions.personal_access_token not set'
        assert self.url, 'JiraOptions.url not set'

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', dest='user',
                        default=None, help='Username to access JIRA')
    parser.add_argument('-t', '--personal-access-token', dest='personal_access_token',
                        default=None, help='Personal Access Token from JIRA')
    parser.add_argument('-j', '--jira-url', dest='url',
                        help='JIRA Tenant base URL (e.g. https://account.atlassian.net)')
    parser.add_argument('--no-verify-ssl', dest='no_verify_ssl', default=False,
                        action='store_true', help='Do not verify SSL certificates for requests')
    parser.add_argument('--action', dest='action', default='get-issue', help='Get an issue from Jira')
    parser.add_argument('issues', nargs='*', help='List of issues by key (e.g. TASK-1, TASK-2, TASK-3, etc.)')
    return parser.parse_args()

if __name__ == '__main__':
    print(JiraOptions(parse_args()) and 'JiraOptions successfully instantiated')
