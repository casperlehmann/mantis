from typing import TYPE_CHECKING
from pathlib import Path
import os
import json
import requests

from .jira_issues import JiraIssues
from .utils import JiraSystemConfigLoader

if TYPE_CHECKING:
    from .jira_auth import JiraAuth
    from .jira_options import JiraOptions

class JiraClient:
    def __init__(self, jira_option: 'JiraOptions', auth: 'JiraAuth',
                 no_cache: bool = False):
        self.options = jira_option
        self.auth = auth.auth
        self.no_verify_ssl = auth.no_verify_ssl
        self.project_name = jira_option.project
        self._no_cache = no_cache
        self.requests_kwargs = {
            'auth': self.auth,
            'headers': {'Content-Type': 'application/json'},
            'verify': (not self.no_verify_ssl)
        }
        self.cache_dir = Path(self.options.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        (self.cache_dir / 'issues').mkdir(exist_ok=True)
        self.drafts_dir = Path(self.options.drafts_dir)
        self.drafts_dir.mkdir(exist_ok=True)
        self.system_config_loader = JiraSystemConfigLoader(self)
        self.issues = JiraIssues(self)

    def write_to_cache(self, file_name: str, contents: str):
        with open(self.cache_dir / file_name, 'w') as f:
            return f.write(contents)

    def remove_from_cache(self, file_name: str):
        os.remove(self.cache_dir / file_name)

    def get_from_cache(self, file_name: str):
        if not (self.cache_dir / file_name).exists():
            return
        with open(self.cache_dir / file_name, 'r') as f:
            return f.read()

    def get_project_keys(self):
        for issue_type in self.issues.allowed_types:
            url = (
                f'issue/createmeta'
                f'?projectKeys={self.project_name}'
                f'&issuetypeNames={issue_type}'
                '&expand=projects.issuetypes.fields'
            )
            response = self._get(url)
            response.raise_for_status()
            data = response.json()
            self.write_to_cache(f'issue_type_fields_{issue_type}.json', json.dumps(data))
        return self.issues.allowed_types

    def write_issue_to_cache(self, key: str, data):
        self.write_to_cache(f'issues/{key}.json', json.dumps(data))

    def get_issue_from_cache(self, key: str):
        if self._no_cache:
            return
        issue_data = self.get_from_cache(f'issues/{key}.json')
        if issue_data:
            return json.loads(issue_data)

    def remove_issue_from_cache(self, key: str):
        self.remove_from_cache(f'issues/{key}.json')

    @property
    def api_url(self):
        assert self.options.url
        return self.options.url + '/rest/api/latest'

    def _get(self, uri, params={}):
        url = f'{self.api_url}/{uri}'
        return requests.get(url, params=params, **self.requests_kwargs)

    def _post(self, uri, data):
        url = f'{self.api_url}/{uri}'
        return requests.post(url, json=data, **self.requests_kwargs)

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
        except requests.exceptions.ConnectionError as e:
            print('Connection error. Run it like this:')
            print("export JIRA_TOKEN=$(cat secret.txt)")
            print("python main.py")
            exit()
        except Exception as e:
            print(e.with_traceback)
            print('\ntest_auth failed for unknown reasons.')
            raise e

