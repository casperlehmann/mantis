from pprint import pprint
import re
import shutil
import requests

from typing import TYPE_CHECKING, Any

from jira.auto_complete import AutoComplete, Suggestion
from jira.jira_issues import JiraIssues
from jira.config_loader import JiraSystemConfigLoader
from jira.jira_auth import JiraAuth

if TYPE_CHECKING:
    from mantis.mantis_client import MantisClient


def process_key(key: str, exception: Exception) -> tuple[str, str]:
    match key.split("-"):
        case (s,):
            raise NotImplementedError(
                f"Partial keys are not supported. Please "
                f'provide the full key for your issue: "PROJ-{s}"'
            ) from exception
        case (project, task_no):
            return (project, task_no)
        case _:
            raise NotImplementedError(
                f'Key contains too many components: "{key}"'
            ) from exception


class JiraClient:

    _project_id: None | str = None

    def __init__(self, mantis: 'MantisClient'):
        self.mantis = mantis
        self.system_config_loader = JiraSystemConfigLoader(self)
        self.issues = JiraIssues(self)
        self.auto_complete = AutoComplete(self)

    def web(self) -> None:
        """Print the web URL of the Jira instance."""
        if not self.mantis.options.url:
            raise ValueError('Jira URL must be set in options')
        print(self.mantis.options.url)

    @property
    def auth(self) -> JiraAuth:
        return JiraAuth(self.mantis.options)

    @property
    def project_name(self) -> str:
        if not self.mantis.options.project:
            raise ValueError('Project name must be set in options')
        return self.mantis.options.project
    
    @property
    def project_id(self) -> str:
        if self._project_id:
            # Will be loaded when downloading issuetypes
            return self._project_id
        projects = self.system_config_loader.get_projects()
        assert isinstance(projects, list), f"To satisfy the type checker. Got: {projects}"
        for project in projects:
            if project.get('key') == self.project_name:
                project_id = project.get('id')
                break
        else:
            raise RuntimeError('Could not find matching project id')
        assert isinstance(project_id, str), f'project_id should be a str. Got: {project_id} ({type(project_id)})'
        assert re.match(r'^[0-9]*$', project_id), f'project_id must be numeric. Got: {project_id}'
        self._project_id = project_id
        return self._project_id

    def get_issuetypes(self) -> dict[str, list[dict[str, Any]]]:
        url = f'issue/createmeta/{self.project_name}/issuetypes'
        response = self.mantis.http._get(url)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e.response.reason)
            print(e.response.content)
            exit()
        issuetypes: dict[str, list[dict[str, Any]]] = response.json()
        assert isinstance(issuetypes, dict), f'issuetypes is not a dict: {issuetypes}'
        assert 'issueTypes' in issuetypes, f"'issueTypes' not in issuetypes. Got keys: {list(issuetypes.keys())}"
        assert isinstance(issuetypes['issueTypes'], list), f"issuetypes['issueTypes'] is not a list. Got: {issuetypes}"
        li = issuetypes['issueTypes']
        assert isinstance(li, list), f"issuetypes['issueTypes'] is not a list. Got: {issuetypes}"
        for x in li:
            for y,z in x.items():
                assert isinstance(y, str)
                assert z is not None, f"key {y} is None"
        return issuetypes

    def issuetype_name_to_id(self, issuetype_name: str) -> str:
        nested_issuetypes = self.system_config_loader.get_issuetypes().get('issueTypes', [{}])
        some_issuetypes = [t for t in nested_issuetypes if t.get('name', '').lower() == issuetype_name.lower()]
        assert len(some_issuetypes) > 0, f"No issuetypes found named {issuetype_name}"
        one_issuetype = some_issuetypes[0]
        issuetype_id = one_issuetype['id']
        return issuetype_id

    def get_createmeta(self, issuetype_id: str) -> dict[str, int | list[dict[str, Any]]]:
        """Createmeta dict with a list of fields called 'fields'"""
        url = f"issue/createmeta/{self.project_name}/issuetypes/{issuetype_id}"
        response = self.mantis.http._get(url)
        response.raise_for_status()
        data = response.json()
        assert isinstance(data, dict)
        assert 'fields' in data.keys(), f'Key "fields" not in data.keys(). Got: {data.keys()} ... {data}'
        return data
    
    def get_editmeta(self, issue_key: str) -> dict[str, Any]:
        # url = f"issue/{issue_key}?expand=editmeta"
        url = f"issue/{issue_key}/editmeta"
        response = self.mantis.http._get(url)
        response.raise_for_status()
        return response.json()

    def get_issue(self, key: str) -> dict[str, dict]:
        response = self.mantis.http._get(f"issue/{key}")
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self.handle_http_error(e, key)
        issue_data: dict[str, dict] = response.json()
        return issue_data

    def post_issue(self, data: dict) -> dict:
        """Post a new issue to Jira"""
        response = self.mantis.http._post("issue", data=data)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e.response.reason)
            print(e.response.json())
            exit()
        return response.json()

    def warmup(self, delete_drafts: bool=False) -> None:
        if delete_drafts:
            if self.mantis.drafts_dir.exists():
                # This violently removes everything. Don't store anything important in the drafts_dir.
                shutil.rmtree(self.mantis.drafts_dir)
                self.mantis.drafts_dir.mkdir(exist_ok=True)
        self.mantis.cache.invalidate()
        self.system_config_loader.get_projects(force_skip_cache = True)
        assert not self.mantis.cache.get_issuetypes_from_system_cache()
        self.system_config_loader.get_issuetypes(force_skip_cache = True)
        assert self.mantis.cache.get_issuetypes_from_system_cache()
        resp = self.system_config_loader.fetch_and_update_all_createmeta()
        pprint(resp)

    def warmup_issues(self, *issue_keys: str) -> None:
        for issue_key in issue_keys:
            self.issues.get(key=issue_key).editmeta
        print(f'Fetched issues: {issue_keys}')

    def get_projects(self) -> list[dict[str, Any]]:
        url = 'project'
        response = self.mantis.http._get(url)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e.response.reason)
            print(e.response.content)
            exit()
        payload: list[dict[str, Any]] = response.json()
        return payload

    def get_current_user(self) -> dict[str, str]:
        response = self.mantis.http._get("myself")
        response.raise_for_status()
        data = response.json()
        return data

    def get_current_user_account_id(self) -> str | None:
        return self.get_current_user().get("accountId")

    def get_current_user_as_assignee(self) -> dict:
        return {"assignee": {"accountId": self.get_current_user_account_id()}}

    def update_field(self, key: str, data: dict) -> bool:
        uri = f"issue/{key}"
        response = self.mantis.http._put(uri, data)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print (e.response.reason )
            print (e.response.json() )
            exit()
        return True

    def jql_auto_complete(self, field_name: str, field_value: str) -> dict[str, Any]:
        uri = "jql/autocompletedata/suggestions"
        query = {
            'fieldName': field_name,
            'fieldValue': field_value,
        }
        response = self.mantis.http._get(uri, query)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print (e.response.reason )
            print (e.response.json() )
            exit()
        return response.json()

    def validate_input(self, search_field: str, search_name: str) -> list[Suggestion]:
        """Validate user input by checking it against the JQL auto-complete endpoint."""
        auto_complete_suggestions = self.auto_complete.get_suggestions(search_field, search_name)
        if len(auto_complete_suggestions) == 0:
            print(f'No results found for {search_field} "{search_name}"')
            return []
        elif len(auto_complete_suggestions) == 1:
            suggestion = auto_complete_suggestions[0]
            print(f'Single match found for {search_field} "{search_name}":')
            print(f'- {suggestion.display_name} ({suggestion.value})')
            return [suggestion]
        else:
            print('Ambiguous result:')
            for suggestion in auto_complete_suggestions:
                print(f'- {suggestion.display_name} ({suggestion.value})')
            return auto_complete_suggestions

    def test_auth(self) -> bool:
        try:
            user = self.get_current_user()
            if not isinstance(user, dict):
                raise ValueError(f"User is should be type dict. Got: {type(user)}")
            print(
                f"Connected as user: {user.get('displayName', 'ERROR: No displayName')}"
            )
            return True
        except requests.exceptions.ConnectionError:
            print("Connection error. Run it like this:")
            print("export JIRA_TOKEN=$(cat secret.txt)")
            print("uv run python main.py")
            exit(1)
        except Exception as e:
            print("test_auth failed for unknown reasons.")
            raise e

    def handle_http_error(self, exception: requests.HTTPError, key: str) -> None:
        (project_from_key, task_no_from_key) = process_key(key, exception)
        match exception.response.reason:
            case "Not Found":
                if " " in key:
                    raise ValueError(
                        f'Whitespace in key is not allowed ("{key}")'
                    ) from exception
                elif not task_no_from_key.isnumeric():
                    raise ValueError(
                        f'Issue number "{task_no_from_key}" in key "{key}" must be numeric'
                    ) from exception
                elif self.mantis.options.project not in key:
                    raise ValueError(
                        f"The requested issue does not exist. Note that the "
                        f'provided key "{key}" does not appear to match '
                        f'your configured project "{self.mantis.options.project}"'
                    ) from exception
                else:
                    raise ValueError(
                        f'The issue "{project_from_key}-{task_no_from_key}" does '
                        f'not exists in the project "{project_from_key}"'
                    ) from exception
            case _:
                raise AttributeError("Unknown reason") from exception

    def get_field_names(self, issue_key: str) -> dict[str, Any]:
        """Fetch the field names for an issue.
        
        https://support.atlassian.com/cloud-automation/docs/find-the-smart-value-for-a-field/
        https://<yourinstanceurl>/rest/api/2/issue/<issuekey>?expand=names
        """
        url = f"issue/{issue_key}?expand=names"
        response = self.mantis.http._get(url)
        response.raise_for_status()
        return response.json()
