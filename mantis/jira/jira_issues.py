from typing import TYPE_CHECKING

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
        response.raise_for_status()
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

