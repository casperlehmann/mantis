from typing import TYPE_CHECKING, Any

from requests.models import HTTPError

if TYPE_CHECKING:
    from .jira_client import JiraClient


def process_key(key: str, exception: Exception) -> tuple[str, str]:
    match key.split("-"):
        case (s,):
            raise NotImplementedError(
                f"Partial keys are not supported. Please "
                f'provide the full key for your issue: "PROJ-{s}"'
            ) from exception
        case (project, task_no):
            return (project, task_no)
        case _:
            raise NotImplementedError(
                f'Key contains too many components: "{key}"'
            ) from exception


class JiraIssue:
    def __init__(self, client: "JiraClient", raw_data: dict[str, dict]) -> None:
        self.client = client
        self.data = raw_data
        # https://docs.pydantic.dev/1.10/datamodel_code_generator/

    def get(self, key: str, default: Any = None) -> dict | None:
        return self.data.get(key, default)

    @property
    def fields(self) -> dict:
        fields = self.data.get("fields")
        if not fields:
            raise KeyError("JiraIssue.data does not have any fields")
        return fields

    def get_field(self, key: str, default: Any = None) -> Any:
        # Note that the key can exist and the value can still be None
        return self.fields.get(key, default)


class JiraIssues:
    _allowed_types = None

    def __init__(self, client: "JiraClient"):
        self.client = client
        # self.load_allowed_types()
        # assert self._allowed_types

    def load_allowed_types(self):
        cached_issuetypes = (
            self.client.system_config_loader.get_issuetypes_for_project()
        )
        if not cached_issuetypes:
            return
        assert isinstance(cached_issuetypes, list)
        assert isinstance(cached_issuetypes[0], dict)
        assert isinstance(cached_issuetypes[0]["id"], str), f'Unexpected type of cached_issuetypes[0]["id"]: {cached_issuetypes[0]["id"]} ({type(cached_issuetypes[0]["id"])})'
        sorted_cached_issuetypes = sorted(
            cached_issuetypes, key=lambda x: str(x.get("id"))
        )
        self._allowed_types = [str(_.get("name")) for _ in sorted_cached_issuetypes]

    @property
    def allowed_types(self):
        if self._allowed_types is None:
            self.load_allowed_types()
        return self._allowed_types

    def get(self, key: str) -> JiraIssue:
        if not self.client._no_read_cache:
            issue_from_cache = self.client.cache.get_issue(key)
            if issue_from_cache:
                return JiraIssue(self.client, issue_from_cache)
        response = self.client.get_issue(key)
        try:
            response.raise_for_status()
        except HTTPError as e:
            self.handle_http_error(e, key)
        data: dict[str, dict] = response.json()
        self.client.cache.write_issue(key, data)
        return JiraIssue(self.client, data)

    def create(self, issue_type: str, title: str, data: dict) -> dict:
        assert self.allowed_types and issue_type in self.allowed_types
        if len(data.keys()) == 0:
            raise ValueError("The data object is an empty payload")
        print(f"Create issue ({issue_type}): {title}")

        response = self.client.post_issue(data)
        from pprint import pprint

        pprint(response.json())
        response.raise_for_status()
        response_data: dict = response.json()
        return response_data

    def handle_http_error(self, exception: HTTPError, key: str) -> None:
        (project_from_key, task_no_from_key) = process_key(key, exception)
        match exception.response.reason:
            case "Not Found":
                if " " in key:
                    raise ValueError(
                        f'Whitespace in key is not allowed ("{key}")'
                    ) from exception
                elif not task_no_from_key.isnumeric():
                    raise ValueError(
                        f'Issue number "{task_no_from_key}" in key "{key}" must be numeric'
                    ) from exception
                elif self.client.options.project not in key:
                    raise ValueError(
                        f"The requested issue does not exist. Note that the "
                        f'provided key "{key}" does not appear to match '
                        f'your configured project "{self.client.options.project}"'
                    ) from exception
                else:
                    raise ValueError(
                        f'The issue "{project_from_key}-{task_no_from_key}" does '
                        f'not exists in the project "{project_from_key}"'
                    ) from exception
            case _:
                raise AttributeError("Unknown reason") from exception
