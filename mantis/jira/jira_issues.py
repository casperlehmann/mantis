from pprint import pprint

from typing import TYPE_CHECKING, Any

from mantis.drafts import Draft

if TYPE_CHECKING:
    from .jira_client import JiraClient


class JiraIssue:
    def __init__(self, client: "JiraClient", raw_data: dict[str, Any]) -> None:
        self.client = client
        self.data = raw_data
        # https://docs.pydantic.dev/1.10/datamodel_code_generator/
        # Only writes if not exists.
        self.draft = Draft(self.client, self)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default) or default

    @property
    def fields(self) -> dict[str, Any]:
        fields = self.data.get("fields")
        if not fields:
            raise KeyError("JiraIssue.data does not have any fields")
        return fields

    def get_field(self, key: str, default: Any = None) -> Any:
        if key in {'ignore', 'header'}:
            return default
        # Guarding against non-existing fields in the source data. This allows us to do only
        # a single None-check below.
        if key not in self.fields:
            raise ValueError(f"key '{key}' not in self.fields (i.e. not present upstream)")
        # Note that the key can exist and the value can still be None.
        # We only want to fall back on the default value when the value is actually None.
        # Boolean values would break if we relied on Truthiness.
        value = self.fields[key]
        return default if value is None else value

    def update_field(self, data: dict[str, Any]) -> None:
        key = self.data.get('key')
        if not key:
            raise ValueError('No key')
        self.client.update_field(key, data)
    

class JiraIssues:
    _allowed_types: list[str] | None = None

    def __init__(self, client: "JiraClient"):
        self.client = client

    def load_allowed_types(self) -> list[str]:
        issuetypes = (
            self.client.system_config_loader.get_issuetypes_for_project()
        )
        if not issuetypes:
            raise ValueError('No values retrieved for issuetypes')
        assert isinstance(issuetypes, dict)
        nested_issuetypes: list[dict] = issuetypes['issueTypes']
        assert isinstance(nested_issuetypes, list), f"nested_issuetypes: {nested_issuetypes}"
        assert isinstance(nested_issuetypes[0], dict)
        assert isinstance(nested_issuetypes[0]["id"], str), f'Unexpected type of nested_issuetypes[0]["id"]: {nested_issuetypes[0]["id"]} ({type(nested_issuetypes[0]["id"])})'
        sorted_nested_issuetypes = sorted(
            nested_issuetypes, key=lambda x: str(x.get("id"))
        )
        assert len(sorted_nested_issuetypes), 'List sorted_nested_issuetypes must not be empty'
        self._allowed_types = [_.get("name", '') for _ in sorted_nested_issuetypes]
        assert self._allowed_types
        return self._allowed_types

    @property
    def allowed_types(self) -> list[str]:
        if self._allowed_types is None:
            self.load_allowed_types()
            if self._allowed_types is None:
                raise ValueError('Loading allowed_types failed.')
        return self._allowed_types

    def get(self, key: str) -> JiraIssue:
        if not self.client._no_read_cache:
            issue_data_from_cache = self.client.cache.get_issue(key)
            if issue_data_from_cache:
                return JiraIssue(self.client, issue_data_from_cache)
        data = self.client.get_issue(key)
        self.client.cache.write_issue(key, data)
        return JiraIssue(self.client, data)

    def create(self, issuetype: str, title: str, data: dict) -> dict:
        assert issuetype in self.allowed_types
        if len(data.keys()) == 0:
            raise ValueError("The data object is an empty payload")
        print(f"Create issue ({issuetype}): {title}")

        response = self.client.post_issue(data)
        pprint(response)
        return response
