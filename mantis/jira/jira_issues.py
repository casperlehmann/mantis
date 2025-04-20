from typing import TYPE_CHECKING

from requests.models import HTTPError

if TYPE_CHECKING:
    from jira_client import JiraClient

def process_key(key: str, exception: Exception) -> tuple[str, str]:
    match key.split('-'):
        case (s,):
            raise NotImplementedError(
                f'Partial keys are not supported. Please '
                f'provide the full key for your issue: "PROJ-{s}"'
            ) from exception
        case (project, task_no):
            return (project, task_no)
        case _:
            raise NotImplementedError(
                f'Key contains too many components: "{key}"'
            ) from exception

class JiraIssues:
    allowed_types = ['Story', 'Sub-Task', 'Epic', 'Bug', 'Task']

    def __init__(self, client: 'JiraClient'):
        self.client = client
        cached_issuetypes = client.system_config_loader.get_issuetypes_names_from_cache()
        if cached_issuetypes:
            assert isinstance(cached_issuetypes, list)
            assert isinstance(cached_issuetypes[0], dict)
            assert isinstance(cached_issuetypes[0]['id'], int)
            sorted_cached_issuetypes = sorted(cached_issuetypes, key=lambda x: str(x.get('id')))
            self.allowed_types = [str(_.get('name')) for _ in sorted_cached_issuetypes]

    def get(self, key: str) -> dict:
        if not self.client._no_cache:
            issue_from_cache = self.client.get_issue_from_cache(key)
            if issue_from_cache:
                return issue_from_cache
        response = self.client.get_issue(key)
        try:
            response.raise_for_status()
        except HTTPError as e:
            self.handle_http_error(e, key)
        data = response.json()
        if not self.client._no_cache:
            self.client.write_issue_to_cache(key, data)
        return data

    def create(self, issue_type, title, data):
        assert issue_type in self.allowed_types
        issue_type = issue_type or data.get('issuetype')
        if len(data.keys()) == 0:
            raise ValueError('The data object is an empty payload')
        print (f'Create issue ({issue_type}): {title}')

        response = self.client.post_issue(data)
        from pprint import pprint
        pprint( response.json())
        response.raise_for_status()
        data = response.json()
        return data

    def handle_http_error(self, exception, key):
        (project_from_key, task_no_from_key) = process_key(key, exception)
        match exception.response.reason:
            case "Not Found":
                if (' ' in key):
                    raise ValueError(
                        f'Whitespace in key is not allowed ("{key}")'
                    ) from exception
                elif (not task_no_from_key.isnumeric()):
                    raise ValueError(
                        f'Issue number "{task_no_from_key}" in key "{key}" must be numeric'
                    ) from exception
                elif self.client.options.project not in key:
                    raise ValueError(
                        f'The requested issue does not exist. Note that the '
                        f'provided key "{key}" does not appear to match '
                        f'your configured project "{self.client.options.project}"'
                    ) from exception
                else:
                    raise ValueError(
                        f'The issue "{project_from_key}-{task_no_from_key}" does '
                        f'not exists in the project "{project_from_key}"'
                    ) from exception
            case _:
                raise exception

