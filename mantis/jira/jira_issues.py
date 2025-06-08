from pprint import pprint

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from mantis.drafts import Draft
from mantis.jira.utils.jira_system_config_loader import CreatemetaModelFactory, EditmetaModelFactory

if TYPE_CHECKING:
    from .jira_client import JiraClient


class JiraIssue:
    """Represents data reflecting an issue in Jira.
    
    An issue may be read, written or editing.
    - Reading means instantiating from the (cached) upstream data.
    - Creating means instantiating based on entered data, ensuring
      conformity with createmeta and pushing upstream.
    - Editing means instantiating from the (cached) upstream data,
      then comparing with entered data while ensuring conformity
      with editmeta before pushing to upstream.
    """
    
    non_meta_fields = ('reporter', 'status')
    non_editmeta_fields = ('project', 'reporter', 'status')
    non_createmeta_fields: tuple[str] = ('',)

    def __init__(self, client: "JiraClient", raw_data: dict[str, Any]) -> None:
        self.client = client
        self.data = raw_data
        # Only writes if not exists.
        self.draft = Draft(self.client, self)
        self._createmeta_factory: CreatemetaModelFactory | None = None
        self._editmeta_factory: EditmetaModelFactory | None = None

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default) or default

    @property
    def key(self) -> str:
        key = self.data.get('key')
        if not key:
            raise ValueError('No key')
        return key

    @property
    def issuetype(self) -> str:
        if not 'issuetype' in self.fields.keys():
            raise ValueError(f'Field "issuetype" not in JiraIssue.data. Available keys: {list(self.data.keys())}')
        return self.data['fields']['issuetype']['name']

    @property
    def createmeta_data(self) -> dict[str, int | list[dict[str, Any]]]:
        self._createmeta_data = self.client.system_config_loader.get_createmeta(self.issuetype)
        return self._createmeta_data

    @property
    def createmeta_factory(self) -> CreatemetaModelFactory:
        if self._createmeta_factory is None:
            self._createmeta_factory = CreatemetaModelFactory(self.createmeta_data)
        return self._createmeta_factory

    @property
    def createmeta(self) -> BaseModel:
        # TODO: Createmeta is shared for all issues of the same type.
        #       Should be loaded into a shared object, not one per Issue
        return self.createmeta_factory.make(self.data)

    @property
    def editmeta_data(self) -> dict[str, Any]:
        return self.client.get_editmeta(self.key)

    @property
    def editmeta_factory(self) -> EditmetaModelFactory:
        # TODO: Consider if editmeta itself should be cached instead.
        if self._editmeta_factory is None:
            self._editmeta_factory = EditmetaModelFactory(self.editmeta_data)
        return self._editmeta_factory

    @property
    def editmeta(self) -> BaseModel:
        return self.editmeta_factory.make(self.data)

    @property
    def fields(self) -> dict[str, Any]:
        fields = self.data.get("fields")
        if not fields:
            raise KeyError("JiraIssue.data does not have any fields")
        return fields

    def get_field(self, key: str, default: Any = None) -> Any:
        """Gets the target field of a cached issue.
        
        If a key is not present in the cached data, this means that the field is not set in
        upstream Jira. The field might exist or it might not. In both cases we return the
        default value (or None if not specified).
        Whether a field is available in Jira or not can be found by looking at the createmeta
        or editmeta endpoints.
        """
        if key not in self.fields:
            print(f"key '{key}' not in self.fields (i.e. not present upstream)")
            return default
        # Field is sure to exist, but it might still have value None.
        value = self.fields[key]
        # Boolean values would break if we relied on Truthiness. Using None identity check instead.
        return default if value is None else value

    def update_field(self, data: dict[str, Any]) -> None:
        self.client.update_field(self.key, data)

    def check_field(self, key: str) -> bool:
        """Check the existance and status of a field in the issue."""
        createmeta_schema = self.createmeta_factory.field_by_key(key)
        editmeta_schema = self.editmeta_factory.field_by_key(key)
        if not (editmeta_schema or createmeta_schema):
            if key == 'reporter':
                # reporter might be disabled:
                # https://community.developer.atlassian.com/t/issue-createmeta-projectidorkey-issuetypes-issuetypeid-does-not-send-the-reporter-field-anymore/80973
                createmeta_type = 'user'
                editmeta_type = 'user'
            elif key == 'status':
                createmeta_type = '?'
                editmeta_type = '?'
            elif key in self.non_meta_fields:
                raise ValueError(f'Expected: Field "{key}" cannot be set.')
            else:
                raise ValueError(f'Field "{key}" is in neither createmeta nor editmeta schema.')
        elif not editmeta_schema:
            assert createmeta_schema
            if key in self.non_editmeta_fields:
                editmeta_type = 'N/A'
                createmeta_type = createmeta_schema['schema']['type']
            else:
                raise ValueError(f'Field {key} is not in editmeta_schema.')
        elif not createmeta_schema:
            if key in self.non_createmeta_fields:
                createmeta_type = 'N/A'
                editmeta_type = editmeta_schema['schema']['type']
            else:
                raise ValueError(f'Field {key} is not in createmeta_schema.')
        else:
            editmeta_type = editmeta_schema['schema']['type']
            createmeta_type = createmeta_schema['schema']['type']
        value_from_draft = self.draft.get(key, None)
        value_from_cache = self.get_field(key)
    

class JiraIssues:
    _allowed_types: list[str] | None = None

    def __init__(self, client: "JiraClient"):
        self.client = client

    def load_allowed_types(self) -> list[str]:
        issuetypes = (
            self.client.system_config_loader.get_issuetypes()
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

    def get(self, key: str, force_skip_cache: bool = False) -> JiraIssue:
        if not self.client._no_read_cache and not force_skip_cache:
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
