import pytest
import requests
from jira import JiraOptions, JiraAuth, JiraClient, parse_args
from jira import fetch_enums
from dataclasses import dataclass

class requestsMock:
    def get(self, *args, **kwargs):
        return self
    def raise_for_status(self):
        return []

    def json(self):
        return [
            {'description': 'Created by Jira Agile - do not edit or delete. Issue type '
                            'for a user story.',
            'id': 6,
            'untranslatedName': 'Story'},
            {'description': "A small piece of work that's part of a larger task.",
            'id': 18,
            'untranslatedName': 'Sub-Task'},
            {'description': 'A collection of related bugs, stories, and tasks.',
            'id': 5,
            'untranslatedName': 'Epic'},
            {'description': 'A problem or error.', 'id': 1, 'untranslatedName': 'Bug'},
            {'description': 'A small, distinct piece of work.', 'id': 3, 'untranslatedName': 'Task'},
            {'description': 'A new feature of the product, which has yet to be developed.',
            'id': 17,
            'untranslatedName': 'New Feature'},
            {'description': 'Service Impacting Event', 'id': 10, 'untranslatedName': 'Incident'}
        ]

@dataclass
class cli:
    user = 'admin@domain.com'
    jira_url = 'https://admin.atlassian.net'
    personal_access_token = 'SECRET'
    no_verify_ssl = False

def test_fetch_enums_mock():
    opts = JiraOptions(parser = cli())
    assert opts.user == 'admin@domain.com'
    assert opts.url == 'https://admin.atlassian.net'
    assert opts.personal_access_token == 'SECRET'
    auth = JiraAuth(opts)
    jira = JiraClient(opts, auth, requestsMock())

    types_filter = lambda d: int(d['id']) < 100 and d['name'] in ('Bug', 'Task', 'Epic', 'Story', 'Incident', 'New Feature', 'Sub-Task')
    mapping = {'id': 'id', 'description': 'description', 'untranslatedName': 'name'}
    cast = {'id': int}
    issue_enums = fetch_enums(jira, endpoint = 'issuetype', filter = types_filter, mapping = mapping, cast = cast)
    assert len(issue_enums) == 7
    issue_type_1_bugs = [_ for _ in issue_enums if _['id'] == 1]
    assert len(issue_type_1_bugs) == 1
    issue_type_1_bug = issue_type_1_bugs[0]
    assert issue_type_1_bug['name'] == 'Bug'
    assert issue_type_1_bug['description'] == 'A problem or error.'

def test_fetch_enums_real():
    opts = JiraOptions()
    assert opts.user != 'admin@domain.com'
    assert opts.url != 'https://admin.atlassian.net'
    assert opts.personal_access_token != 'SECRET'
    auth = JiraAuth(opts)
    jira = JiraClient(opts, auth, requests)

    types_filter = lambda d: int(d['id']) < 100 and d['name'] in ('Bug', 'Task', 'Epic', 'Story', 'Incident', 'New Feature', 'Sub-Task')
    mapping = {'id': 'id', 'description': 'description', 'untranslatedName': 'name'}
    cast = {'id': int}
    issue_enums = fetch_enums(jira, endpoint = 'issuetype', filter = types_filter, mapping = mapping, cast = cast)
    assert len(issue_enums) == 7
    issue_type_1_bugs = [_ for _ in issue_enums if _['id'] == 1]
    assert len(issue_type_1_bugs) == 1
    issue_type_1_bug = issue_type_1_bugs[0]
    assert issue_type_1_bug['name'] == 'Bug'
    assert issue_type_1_bug['description'] == 'A problem or error.'
    