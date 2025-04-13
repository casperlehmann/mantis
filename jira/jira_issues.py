from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jira_client import JiraClient

class JiraIssues:
    allowed_types = {'Story', 'Sub-Task', 'Epic', 'Bug', 'Task'}

    def __init__(self, client: 'JiraClient'):
        self.client = client

    def get(self, key: str) -> dict:
        response = self.client.get_issue(key)
        response.raise_for_status()
        data = response.json()
        assert data.get('key', 'NO_KEY_IN_RESPONSE_PAYLOAD') == key 
        return data

