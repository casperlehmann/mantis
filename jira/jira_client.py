import requests

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jira.jira_auth import JiraAuth
    from jira.cli import JiraOptions

class JiraClient:
    def __init__(self, jira_option: 'JiraOptions', auth: 'JiraAuth', request_handler):
        self.options = jira_option
        self.auth = auth.auth
        self.no_verify_ssl = auth.no_verify_ssl
        self.request_handler = request_handler
        # self.issue = JiraIssue(self, jira_option, auth)

    @property
    def api_url(self):
        assert self.options.url
        return self.options.url + '/rest/api/latest'

    def _get(self, uri, params={}):
        headers = {'Content-Type': 'application/json'}
        url = self.api_url + uri
        return self.request_handler.get(url, params=params, auth=self.auth, headers=headers, verify=(not self.no_verify_ssl))

    def get_current_user(self) -> dict:
        response = self._get('/myself')
        response.raise_for_status()
        data = response.json()
        return data

    def test_auth(self):
        try:
            user = self.get_current_user()
            print(f'Connected as user: {user.get('displayName', 'ERROR: No displayName')}')
        except requests.exceptions.ConnectionError as e:
            print('Connection error. Run it like this:')
            print("export JIRA_TOKEN=$(cat secret.txt)")
            print("python main.py")
            exit()
        except Exception as e:
            print(e.with_traceback)
            print('\ntest_auth failed for unknown reasons.')
            raise e
