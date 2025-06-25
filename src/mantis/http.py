import requests

from typing import TYPE_CHECKING, Any

from mantis.jira.jira_auth import JiraAuth

if TYPE_CHECKING:
    from requests.auth import HTTPBasicAuth
    from mantis.mantis_client import MantisClient

class Http:
    """
    A class to handle HTTP requests and responses.
    """

    def __init__(
        self, mantis: 'MantisClient', auth: 'JiraAuth', no_read_cache: bool = False
    ):
        self.options = mantis.options
        self.auth = auth.auth
        self.no_verify_ssl = auth.no_verify_ssl
        self.requests_kwargs: dict[str, 'HTTPBasicAuth | bool | dict[str, Any]'] = {
            "auth": self.auth,
            "headers": {"Content-Type": "application/json"},
            "verify": (not self.no_verify_ssl),
        }

    @property
    def api_url(self) -> str:
        assert self.options.url
        return self.options.url + "/rest/api/latest"

    def _get(self, uri: str, params: dict = {}) -> requests.Response:
        """
        Perform a GET request to the specified URL with optional parameters.

        :param url: The URL to send the GET request to.
        :param params: Optional dictionary of query parameters.
        :return: The response text from the GET request.
        """
        url = f"{self.api_url}/{uri}"
        return requests.get(url, params=params, **self.requests_kwargs)  # type: ignore


    def post(url: str, data: dict = None) -> str:
        """
        Perform a POST request to the specified URL with optional data.

        :param url: The URL to send the POST request to.
        :param data: Optional dictionary of data to send in the POST request.
        :return: The response text from the POST request.
        """
        import requests
        response = requests.post(url, json=data)
        return response.text
    

    def _post(self, uri: str, data: dict) -> requests.Response:
        url = f"{self.api_url}/{uri}"
        return requests.post(url, json=data, **self.requests_kwargs)  # type: ignore

    def _put(self, uri: str, data: dict) -> requests.Response:
        url = f"{self.api_url}/{uri}"
        return requests.put(url, json=data, **self.requests_kwargs)  # type: ignore
