import requests

from requests.auth import HTTPBasicAuth

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jira.jira_options import JiraOptions

class JiraAuth:
    def __init__(self, options: 'JiraOptions') -> None:
        self.options = options
        assert self.options.url

    @property
    def auth(self):
        if self.options.personal_access_token:
            assert self.options.user
            return HTTPBasicAuth(self.options.user, self.options.personal_access_token)
        raise PermissionError
