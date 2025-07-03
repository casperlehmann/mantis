from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from jira.jira_client import JiraClient


class Suggestion:
    def __init__(self, entry: dict[str, str]): # display_name: str, value: str):
        assert entry.get('displayName')
        self.display_name = entry['displayName'].replace('<b>', '').replace('</b>', '')
        self.value = entry.get('value')

    def __repr__(self) -> str:
        return f"Suggestion(display_name={self.display_name}, value={self.value})"


class AutoComplete:
    def __init__(self, jira: "JiraClient") -> None:
        self.jira = jira

    def get_suggestions(self, field_name: str, field_value: str) -> list[Suggestion]:
        data = self.jira.jql_auto_complete(field_name, field_value)
        return [Suggestion(entry) for entry in data.get('results', [])]
