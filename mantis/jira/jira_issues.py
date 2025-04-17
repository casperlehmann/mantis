from typing import TYPE_CHECKING

from requests.models import HTTPError

if TYPE_CHECKING:
    from jira_client import JiraClient

def process_key(key: str):
    split_key = key.split('-')
    match split_key:
        case (s,):
            raise NotImplementedError(f'Key: {s}')
        case (project, task_no):
            return (project, task_no)
        case _:
            NotImplementedError(f'Key: {key}')

class JiraIssues:
    allowed_types = {'Story', 'Sub-Task', 'Epic', 'Bug', 'Task'}

    def __init__(self, client: 'JiraClient'):
        self.client = client
        cached_issuetypes = client.get_issuetypes_names_from_cache()
        if cached_issuetypes:
            self.allowed_types = {_.get('name') for _ in cached_issuetypes}

    def get(self, key: str) -> dict:
        issue_from_cache = self.client.get_issue_from_cache(key)
        if issue_from_cache:
            return issue_from_cache
        response = self.client.get_issue(key)
        try:
            response.raise_for_status()
        except HTTPError as e:
            for _ in dir(e): print (_)
            print (e.response.status_code)
            print (e.response.reason)
            match e.response.reason:
                case "Not Found":
                    (project_from_key, task_no_from_key) = process_key(key)
                    assert project_from_key, "No project?"
                    assert task_no_from_key , "No task number?"
                    if self.client.options.project not in key:
                        raise ValueError(f'The requested issue does not exists. Note that the provided key "{key}" does not appear to match your configured project "{self.client.options.project}".') from e
                    else:
                        raise e
                case _:
                    raise e
        data = response.json()
        assert data.get('key', 'NO_KEY_IN_RESPONSE_PAYLOAD') == key 
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

