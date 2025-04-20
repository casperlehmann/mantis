import json
from pprint import pprint

from typing import TYPE_CHECKING, Mapping
from mantis.jira.utils.jira_types import IssueTypeFields, ProjectFieldKeys

from datamodel_code_generator import InputFileType, generate
from datamodel_code_generator import DataModelType

if TYPE_CHECKING:
    from jira_client import JiraClient

def fetch_enums(jira: 'JiraClient',
                endpoint = 'issuetype',
                filter = None,
                mapping = {},
                caster_functions = {}
                ) -> list:
    """Get the enums of the fields in a jira tenant

    Args:
        jira (_type_): Client for connecting to the endpoint.
        endpoint (str, optional): The endpoint for the specific field. Defaults to 'issuetype'.
        filter (_type_, optional): Filters the return value if set. Defaults to None.
        mapping (dict, optional): Renames an internal field name in the Jira api to something custom. Defaults to {}.
        caster_functions (dict, optional): Casts fields using custom conversion functions. Defaults to {}.

    Returns:
        _type_: _description_

    Example for /rest/api/2/issuetype:
        types_filter = lambda d: int(d['id']) < 100 and d['name'] in ('Bug', 'Task', 'Epic', 'Story', 'Incident', 'New Feature', 'Sub-Task')
        mapping = {'id': 'id', 'description': 'description', 'untranslatedName': 'name'}
        caster_functions = {'id': int}
        issue_enums = fetch_enums(jira, endpoint = 'issuetype', filter = types_filter, mapping = mapping, caster_functions = caster_functions)

    See https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-types/#api-rest-api-2-issuetype-get
    """
    response = jira._get(f'/{endpoint}')
    response.raise_for_status()
    data = response.json()
    schemas = []
    for entry in data:
        schema = {}
        if mapping:
            for api_name, rename in mapping.items():
                cast = caster_functions.get(rename, lambda unchanged: unchanged)
                api_value = cast(entry.get(api_name))
                schema[rename] = api_value
        else:
            for api_name, api_value in entry.items():
                cast = caster_functions.get(api_name, lambda unchanged: unchanged)
                api_value = cast(entry.get(api_name))
                schema[api_name] = api_value
        if not filter or filter(schema):
            schemas.append(schema)
    return schemas

class JiraSystemConfigLoader:
    def __init__(self, client: 'JiraClient') -> None:
        self.client = client

    def write_to_system_cache(self, file_name: str, issue_enums) -> None:
        self.client.write_to_cache(f'system/{file_name}', issue_enums)

    def get_from_system_cache(self, file_name: str) -> str | None:
        return self.client.get_from_cache(f'system/{file_name}')

    def get_from_system_cache_decoded(self, file_name: str) -> dict:
        return self.client.get_from_cache_decoded(f'system/{file_name}')

    def loop_issue_type_fields(self):
        for file in self.client.cache_issue_type_fields_dir.iterdir():
            yield file

    def update_issuetypes_cache(self) -> None:
        types_filter = lambda d: int(d['id']) < 100 and d['name'] in (
            'Bug', 'Task', 'Epic', 'Story', 'Sub-Task',
            #'Incident', 'New Feature'
        )
        mapping = {'id': 'id', 'description': 'description', 'untranslatedName': 'name'}
        caster_functions = {'id': int}
        issue_enums = fetch_enums(
            self.client,
            endpoint = 'issuetype',
            filter = types_filter,
            mapping = mapping,
            caster_functions = caster_functions
        )
        self.write_to_system_cache('issue_types.json', json.dumps(issue_enums))

    def get_issuetypes_names_from_cache(self) -> list[dict[str, int|str]] | None:
        issuetypes = self.get_from_system_cache('issue_types.json')
        if issuetypes:
            return json.loads(issuetypes)

    def update_project_field_keys(self) -> list[str]:
        for issue_type in self.client.issues.allowed_types:
            url = (
                f'issue/createmeta'
                f'?projectKeys={self.client.project_name}'
                f'&issuetypeNames={issue_type}'
                '&expand=projects.issuetypes.fields'
            )
            response = self.client._get(url)
            response.raise_for_status()
            data = response.json()
            self.write_to_system_cache(
                f'issue_type_fields/{issue_type}.json', json.dumps(data))
        return self.client.issues.allowed_types

    def compile_plugins(self):
        for input_file in self.loop_issue_type_fields():
            with open(input_file, 'r') as f:
                content = f.read()
            # Remove the .json extension
            name = input_file.name[:-5].replace('-', '_').replace('_', '_').lower()
            output_path = self.client.plugins_dir / f'{name}.py'
            generate(
                content,
                input_file_type = InputFileType.Json,
                input_filename = input_file,
                output=output_path,
                output_model_type=DataModelType.PydanticV2BaseModel,
            )

    def get_all_keys_from_nested_dicts(
            self, data: Mapping[str, ProjectFieldKeys]) -> set[str]:
        d: dict[str, list[str]] = {}
        all_field_keys: set[str] = set()
        for issue_type, field_keys in data.items():
            d[issue_type] = field_keys.fields
            all_field_keys = all_field_keys.union(set(d[issue_type]))
        return all_field_keys

    def print_table(self, column_order: list[str], all_field_keys: set[str],
                    issue_type_field_map: Mapping[str, ProjectFieldKeys]) -> None:
        def print_header_footer():
            print (f'{'':<20} - ', end='')
            for issue_type_name in column_order:
                if not issue_type_name in issue_type_field_map.keys():
                    raise ValueError('column_order contains non-existent key')
                print (f'{issue_type_name:<10}', end = '')
            print()
        print_header_footer()
        for each in all_field_keys:
            print (f'{each:<20} - ', end='')
            for _, project_field_keys in issue_type_field_map.items():
                print (f'{'1   ' if each in project_field_keys.fields
                                 else '' :<10}', end = '')
            print()
        print_header_footer()

    def get_project_field_keys_from_cache(self) -> Mapping[str, ProjectFieldKeys]:
        d: Mapping[str, ProjectFieldKeys] = {}
        for issue_type in self.client.issues.allowed_types:
            try:
                loaded_json = self.get_from_system_cache_decoded(
                    f'issue_type_fields/{issue_type}.json')
                issue_type_fields = IssueTypeFields(loaded_json)
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    f'Cached values do not exist for {issue_type}') from e
            d[issue_type] = ProjectFieldKeys(issue_type, issue_type_fields)
        return d

    def inspect(self) -> None:
        data = self.get_project_field_keys_from_cache()
        all_keys = self.get_all_keys_from_nested_dicts(data)
        self.print_table(self.client.issues.allowed_types, all_keys, data)

