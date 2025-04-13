#!/usr/bin/env python

import requests
import json
import requests

from pprint import pprint
from typing import TYPE_CHECKING

from jira import JiraClient, JiraOptions, JiraAuth, parse_args
from jira import fetch_enums

import json

def log(*args):
    print(*args, file=sys.stderr)

if __name__ == '__main__':
    jira_options = JiraOptions(parse_args(), 'options.toml')
    auth = JiraAuth(jira_options)
    jira = JiraClient(jira_options, auth, requests)
    jira.test_auth()

    if jira_options.action == 'fetch-issuetypes':
        types_filter = lambda d: int(d['id']) < 100 and d['name'] in ('Bug', 'Task', 'Epic', 'Story', 'Incident', 'New Feature', 'Sub-Task')
        mapping = {'id': 'id', 'description': 'description', 'untranslatedName': 'name'}
        caster_functions = {'id': int}
        issue_enums = fetch_enums(jira, endpoint = 'issuetype', filter = types_filter, mapping = mapping, caster_functions = caster_functions)
        jira.write_to_cache('issue_types.json', json.dumps(issue_enums))
        pprint(jira.get_from_cache('issue_types.json'))
    elif jira_options.action == 'get-issue':
        for issue_key in jira_options.issues:
            issue = jira.issues.get(key=issue_key)
            key = issue.get('key', 'N/A')
            title = issue.get('fields', {}).get('summary')
            print(f'[{key}] {title}')

