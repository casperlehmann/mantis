import json

from typing import TYPE_CHECKING

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

    def get_from_system_cache(self, file_name: str) -> None:
        return self.client.get_from_cache(f'system/{file_name}')

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

    def get_issuetypes_names_from_cache(self) -> set[str]:
        issuetypes = self.get_from_system_cache('issue_types.json')
        if issuetypes:
            return json.loads(issuetypes)

    def get_project_keys(self) -> set[str]:
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
            self.write_to_system_cache(f'issue_type_fields/{issue_type}.json', json.dumps(data))
        return self.client.issues.allowed_types

