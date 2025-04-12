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
    def jira_url(self):
        return self.options.jira_url

    @property
    def no_verify_ssl(self):
        return self.options.no_verify_ssl

    @property
    def user(self):
        return self.options.user

    @property
    def personal_access_token(self):
        return self.options.personal_access_token

    @property
    def auth(self):
        if self.personal_access_token:
            assert self.options.user
            return HTTPBasicAuth(self.user, self.personal_access_token)
        raise PermissionError
