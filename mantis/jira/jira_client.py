import requests

from pathlib import Path
from typing import TYPE_CHECKING, Any

from mantis.jira.jira_issues import JiraIssues
from mantis.jira.utils import Cache, JiraSystemConfigLoader

if TYPE_CHECKING:
    from requests.auth import HTTPBasicAuth
    from mantis.jira.jira_auth import JiraAuth
    from mantis.jira.jira_options import JiraOptions


class JiraClient:
    def __init__(
        self, jira_option: "JiraOptions", auth: "JiraAuth", no_cache: bool = False
    ):
        self.options = jira_option
        self.auth = auth.auth
        self.no_verify_ssl = auth.no_verify_ssl
        self._no_read_cache = no_cache
        self.requests_kwargs: dict[str, 'HTTPBasicAuth | bool | dict[str, Any]'] = {
            "auth": self.auth,
            "headers": {"Content-Type": "application/json"},
            "verify": (not self.no_verify_ssl),
        }
        self.cache = Cache(self)
        self.drafts_dir.mkdir(exist_ok=True)
        self.plugins_dir.mkdir(exist_ok=True)
        self.system_config_loader = JiraSystemConfigLoader(self)
        self.issues = JiraIssues(self)

    @property
    def drafts_dir(self) -> Path:
        return Path(self.options.drafts_dir)

    @property
    def plugins_dir(self) -> Path:
        return Path(self.options.plugins_dir)

    @property
    def project_name(self) -> str:
        return self.options.project
    
    @property
    def api_url(self) -> str:
        assert self.options.url
        return self.options.url + "/rest/api/latest"

    def _get(self, uri: str, params: dict = {}) -> requests.Response:
        url = f"{self.api_url}/{uri}"
        return requests.get(url, params=params, **self.requests_kwargs)  # type: ignore

    def _post(self, uri: str, data: dict) -> requests.Response:
        url = f"{self.api_url}/{uri}"
        return requests.post(url, json=data, **self.requests_kwargs)  # type: ignore

    def get_issue(self, key: str) -> requests.Response:
        return self._get(f"issue/{key}")

    def post_issue(self, data: dict) -> requests.Response:
        return self._post("issue", data=data)

    def get_current_user(self) -> dict[str, str]:
        response = self._get("myself")
        response.raise_for_status()
        data = response.json()
        return data

    def get_current_user_account_id(self) -> str | None:
        return self.get_current_user().get("accountId")

    def get_current_user_as_assignee(self) -> dict:
        return {"assignee": {"accountId": self.get_current_user_account_id()}}

    def test_auth(self) -> bool:
        try:
            user = self.get_current_user()
            print(
                f"Connected as user: {user.get('displayName', 'ERROR: No displayName')}"
            )
            return True
        except requests.exceptions.ConnectionError:
            print("Connection error. Run it like this:")
            print("export JIRA_TOKEN=$(cat secret.txt)")
            print("python main.py")
            exit(1)
        except Exception as e:
            print("test_auth failed for unknown reasons.")
            raise e
