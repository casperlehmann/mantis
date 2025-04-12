import argparse
import tomllib

class JiraOptions:
    """Collects options from toml file, allowing for command line overrides
    
    python jira/jira_options.py --user user@domain.com --personal-access-token $JIRA_TOKEN --jira-url=https://account.atlassian.net
    """

    def __init__(self, parser: 'argparse.Namespace' = None, toml_source: str = "options.toml", ):
        with open(toml_source, "rb") as f:
            options = tomllib.load(f)
        self.user = parser and parser.user or options.get('jira', {}).get('user')
        self.personal_access_token = parser and parser.personal_access_token or options.get('jira', {}).get('personal-access-token')
        self.url = parser and parser.jira_url or options.get('jira', {}).get('url')
        assert self.user, 'JiraOptions.user not set'
        assert self.personal_access_token, 'JiraOptions.personal_access_token not set'
        assert self.url, 'JiraOptions.url not set'

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', dest='user',
                        default=None, help='Username to access JIRA')
    parser.add_argument('-t', '--personal-access-token', dest='personal_access_token',
                        default=None, help='Personal Access Token from JIRA')
    parser.add_argument('-j', '--jira-url', dest='jira_url',
                        default='https://account.atlassian.net', help='JIRA Tenant base URL (e.g. https://account.atlassian.net)')
    return parser.parse_args()

if __name__ == '__main__':
    print(JiraOptions(parse_args()) and 'JiraOptions successfully instantiated')
