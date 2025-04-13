from os.path import exists
from requests.exceptions import ConnectionError

from typing import TYPE_CHECKING
from pathlib import Path
import json

from .jira_issues import JiraIssues
from .utils import fetch_enums

if TYPE_CHECKING:
    from jira.jira_auth import JiraAuth
    from jira.cli import JiraOptions

class JiraClient:
    def __init__(self, jira_option: 'JiraOptions', auth: 'JiraAuth', request_handler):
        self.options = jira_option
        self.auth = auth.auth
        self.no_verify_ssl = auth.no_verify_ssl
        self.request_handler = request_handler
        self.requests_kwargs = {
            'auth': self.auth,
            'headers': {'Content-Type': 'application/json'},
            'verify': (not self.no_verify_ssl)
        }
        self.cache_dir = Path(self.options.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        (self.cache_dir / 'issues').mkdir(exist_ok=True)
        self.issues = JiraIssues(self)

    def write_to_cache(self, file_name: str, contents: str):
        with open(self.cache_dir / file_name, 'w') as f:
            return f.write(contents)

    def get_from_cache(self, file_name: str):
        if not (self.cache_dir / file_name).exists():
            return
        with open(self.cache_dir / file_name, 'r') as f:
            return f.read()

    def update_issuetypes_cache(self):
        types_filter = lambda d: int(d['id']) < 100 and d['name'] in ('Bug', 'Task', 'Epic', 'Story', 'Incident', 'New Feature', 'Sub-Task')
        mapping = {'id': 'id', 'description': 'description', 'untranslatedName': 'name'}
        caster_functions = {'id': int}
        issue_enums = fetch_enums(self, endpoint = 'issuetype', filter = types_filter, mapping = mapping, caster_functions = caster_functions)
        self.write_to_cache('issue_types.json', json.dumps(issue_enums))

    def get_issuetypes_names_from_cache(self):
        issuetypes = self.get_from_cache('issue_types.json')
        if issuetypes:
            return json.loads(issuetypes)

    def write_issue_to_cache(self, key: str, data):
        self.write_to_cache(f'issues/{key}.json', json.dumps(data))

    def get_issue_from_cache(self, key: str):
        issue_data = self.get_from_cache(f'issues/{key}.json')
        if issue_data:
            return json.loads(issue_data)

    @property
    def api_url(self):
        assert self.options.url
        return self.options.url + '/rest/api/latest'

    def _get(self, uri, params={}):
        url = f'{self.api_url}/{uri}'
        return self.request_handler.get(url, params=params, **self.requests_kwargs)

    def _post(self, uri, data):
        url = f'{self.api_url}/{uri}'
        return self.request_handler.post(url, json=data, **self.requests_kwargs)

    def get_issue(self, key):
        return self._get(f'issue/{key}')

    def post_issue(self, data):
        return self._post('issue', data=data)

    def get_current_user(self) -> dict:
        response = self._get('myself')
        response.raise_for_status()
        data = response.json()
        return data

    def get_current_user_account_id(self) -> str:
        return self.get_current_user().get('accountId')

    def get_current_user_as_assignee(self) -> dict:
        return {"assignee": {"accountId": self.get_current_user_account_id()}}

    def test_auth(self):
        try:
            user = self.get_current_user()
            print(f'Connected as user: {user.get('displayName', 'ERROR: No displayName')}')
        except ConnectionError as e:
            print('Connection error. Run it like this:')
            print("export JIRA_TOKEN=$(cat secret.txt)")
            print("python main.py")
            exit()
        except Exception as e:
            print(e.with_traceback)
            print('\ntest_auth failed for unknown reasons.')
            raise e
