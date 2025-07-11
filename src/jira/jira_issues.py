from pprint import pprint

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from drafts import Draft
from jira.config_loader.meta_model_factories import CreatemetaModelFactory, EditmetaModelFactory
from jira.issue_field import IssueField

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

    def __init__(self, jira: "JiraClient", raw_data: dict[str, Any]) -> None:
        self.jira = jira
        self.data = raw_data
        # Only writes if not exists.
        self.draft = Draft(self.jira.mantis, self)
        self._createmeta_factory: CreatemetaModelFactory | None = None
        self._editmeta_factory: EditmetaModelFactory | None = None
        self._editmeta: Any | None = None

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
        if 'issuetype' not in self.fields.keys():
            raise ValueError(f'Field "issuetype" not in JiraIssue.data. Available keys: {list(self.data.keys())}')
        return self.data['fields']['issuetype']['name']

    @property
    def createmeta_data(self) -> dict[str, int | list[dict[str, Any]]]:
        return self.jira.system_config_loader.get_createmeta(self.issuetype)

    @property
    def createmeta_factory(self) -> CreatemetaModelFactory:
        if self._createmeta_factory is None:
            self._createmeta_factory = CreatemetaModelFactory(self.createmeta_data, self.issuetype, self.jira)
        return self._createmeta_factory

    @property
    def createmeta(self) -> BaseModel:
        # TODO: Createmeta is shared for all issues of the same type.
        #       Should be loaded into a shared object, not one per Issue
        return self.createmeta_factory.make(self.data)

    @property
    def editmeta_data(self) -> dict[str, Any]:
        return self.jira.system_config_loader.get_editmeta(self.key)

    @property
    def editmeta_factory(self) -> EditmetaModelFactory:
        # TODO: Consider if editmeta itself should be cached instead.
        if self._editmeta_factory is None:
            self._editmeta_factory = EditmetaModelFactory(self.editmeta_data, self.issuetype, self.jira, self.key)
        return self._editmeta_factory

    @property
    def editmeta(self) -> BaseModel:
        if not self._editmeta:
            self._editmeta = self.editmeta_factory.make(self.data)
        return self._editmeta

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
            # print(f"key '{key}' not in self.fields (i.e. not present upstream)")
            return default
        # Field is sure to exist, but it might still have value None.
        value = self.fields[key]
        # Boolean values would break if we relied on Truthiness. Using None identity check instead.
        return default if value is None else value

    def update_field(self, data: dict[str, Any]) -> None:
        """Update a field in the issue with the given data
        
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-put
        """
        self.jira.update_field(self.key, data)

    def update_from_draft(self) -> None:
        """Update the issue in Jira, using the data from its draft."""
        fields = {}
        for draft_field_key, value_from_draft in self.draft.iter_draft_field_items():
            field = IssueField(self, draft_field_key)
            fields.update(field.collect_field_for_update())
        # To-do: Check whether the description has been updated before posting it
        if input(f'Overwrite description of issue [{self.key}] "{self.get_field('description')}"? (y/n): ').lower() in ('y', 'yes'):
            fields['description'] = self.draft.content
        if fields:
            print(f'Updating {', '.join(fields.keys())} with data: ({fields})')
            data = {
                "fields": fields
            }
            self.update_field(data)
            print(f'Reloading {self.key}')
            self.reload_issue()

    def diff_issue_from_draft(self) -> None:
        for draft_field_key, value_from_draft in self.draft.iter_draft_field_items():
            value_from_cache = self.get_field(draft_field_key, None)
            field = IssueField(self, draft_field_key)
            field.check_field()
        print()
        for draft_field_key, value_from_draft in self.draft.iter_draft_field_items():
            value_from_cache = self.get_field(draft_field_key, None)
            print(f"# {self.key} ", end="")
            if value_from_cache is None:
                extracted_from_cache = 'None'
            else:
                extracted_from_cache = value_from_cache if isinstance(value_from_cache, str) else value_from_cache.get('displayName') or value_from_cache.get('name')
            if not value_from_draft:  # E.g. parent not set
                print(f'| Not set   ({draft_field_key}) is None')
            elif not value_from_draft or value_from_draft == 'None' or value_from_draft == {draft_field_key: None}:
                print(f'| None      ({draft_field_key}) is None')
            elif value_from_cache == 'N/A':
                print(f'| Miss      ({draft_field_key}) not found in cache')
            elif not value_from_cache:
                print(f'| Null      ({draft_field_key}) in cache but None')
            elif value_from_cache == 'None':
                print(f'| Field     ({draft_field_key}) not found in cache')
            elif value_from_draft == value_from_cache:
                print(f"| Same      ({draft_field_key}): {value_from_draft}")
            elif value_from_draft == extracted_from_cache:
                print(f"| Extracted ({draft_field_key}): {value_from_draft}")
            else:
                print(f"| Different: {draft_field_key}:")
                # print(f"{value_from_draft}")
                # pprint(value_from_cache)
                # input()

    def reload_issue(self) -> None:
        self.jira.issues.get(self.key, force_skip_cache=True)


class JiraIssues:
    _allowed_types: list[str] | None = None

    def __init__(self, jira: "JiraClient"):
        self.jira = jira

    def load_allowed_types(self) -> list[str]:
        issuetypes = (
            self.jira.system_config_loader.get_issuetypes()
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
        if not self.jira.mantis._no_read_cache and not force_skip_cache:
            issue_data_from_cache = self.jira.mantis.cache.get_issue(key)
            if issue_data_from_cache:
                return JiraIssue(self.jira, issue_data_from_cache)
        data = self.jira.get_issue(key)
        self.jira.mantis.cache.write_issue(key, data)
        return JiraIssue(self.jira, data)

    def create(self, issuetype: str, title: str, data: dict) -> dict:
        """Create a new issue in Jira
        
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post
        """
        assert issuetype in self.allowed_types
        issuetype_id = self.jira.issuetype_name_to_id(issuetype)
        if 'issuetype' not in data:
            data['issuetype'] = {'id': issuetype_id}
        if 'summary' not in data:
            data['summary'] = title
        data['project'] = {'id': self.jira.project_id}
        assert title == data['summary'], 'The "title" parameter must match the "summary" in the data object'
        print(f"Creating issue ({issuetype}): {title}")
        response = self.jira.post_issue({'fields': data})
        issue_key = response["key"]
        print(f'Created issue: [{issue_key}]')
        pprint(response)
        print(f'Reloading {issue_key}')
        self.get(issue_key).reload_issue()
        return response
