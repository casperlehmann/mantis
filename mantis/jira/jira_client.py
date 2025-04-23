import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import requests

from mantis.jira.utils import Cache

from .jira_issues import JiraIssues
from .utils import JiraSystemConfigLoader

if TYPE_CHECKING:
    from .jira_auth import JiraAuth
    from .jira_options import JiraOptions


class JiraClient:
    def __init__(
        self, jira_option: "JiraOptions", auth: "JiraAuth", no_cache: bool = False
    ):
        self.options = jira_option
        self.auth = auth.auth
        self.no_verify_ssl = auth.no_verify_ssl
        self.project_name = jira_option.project
        self._no_cache = no_cache
        self.requests_kwargs = {
            "auth": self.auth,
            "headers": {"Content-Type": "application/json"},
            "verify": (not self.no_verify_ssl),
        }
        self.cache = Cache(self)
        self.drafts_dir = Path(self.options.drafts_dir)
        self.drafts_dir.mkdir(exist_ok=True)
        self.plugins_dir = Path(self.options.plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.system_config_loader = JiraSystemConfigLoader(self)
        self.issues = JiraIssues(self)

    @property
    def api_url(self):
        assert self.options.url
        return self.options.url + "/rest/api/latest"

    def _get(self, uri, params={}):
        url = f"{self.api_url}/{uri}"
        return requests.get(url, params=params, **self.requests_kwargs)

    def _post(self, uri, data):
        url = f"{self.api_url}/{uri}"
        return requests.post(url, json=data, **self.requests_kwargs)

    def get_issue(self, key):
        return self._get(f"issue/{key}")

    def post_issue(self, data):
        return self._post("issue", data=data)

    def get_current_user(self) -> dict:
        response = self._get("myself")
        response.raise_for_status()
        data = response.json()
        return data

    def get_current_user_account_id(self) -> str:
        return self.get_current_user().get("accountId")

    def get_current_user_as_assignee(self) -> dict:
        return {"assignee": {"accountId": self.get_current_user_account_id()}}

    def test_auth(self):
        try:
            user = self.get_current_user()
            print(
                f"Connected as user: {user.get('displayName', 'ERROR: No displayName')}"
            )
        except requests.exceptions.ConnectionError as e:
            print("Connection error. Run it like this:")
            print("export JIRA_TOKEN=$(cat secret.txt)")
            print("python main.py")
            exit()
        except Exception as e:
            print(e.with_traceback)
            print("\ntest_auth failed for unknown reasons.")
            raise e
