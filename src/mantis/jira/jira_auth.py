from requests.auth import HTTPBasicAuth

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantis.options_loader import OptionsLoader


class JiraAuth:
    def __init__(self, options: "OptionsLoader") -> None:
        self.options = options
        assert self.options.url

    @property
    def no_verify_ssl(self) -> bool:
        return self.options.no_verify_ssl

    @property
    def user(self) -> str:
        return self.options.user

    @property
    def personal_access_token(self) -> str:
        return self.options.personal_access_token

    @property
    def auth(self) -> HTTPBasicAuth:
        if self.personal_access_token:
            assert self.options.user
            return HTTPBasicAuth(self.user, self.personal_access_token)
        raise PermissionError
