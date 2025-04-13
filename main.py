#!/usr/bin/env python

import requests
import json
import requests

from pprint import pprint

from jira import JiraClient, JiraOptions, JiraAuth, parse_args

import json

def log(*args):
    print(*args, file=sys.stderr)

if __name__ == '__main__':
    jira_options = JiraOptions(parse_args(), 'options.toml')
    auth = JiraAuth(jira_options)
    jira = JiraClient(jira_options, auth, requests)

    if jira_options.action == 'test-auth':
        jira.test_auth()
    elif jira_options.action == 'me-as-assignee':
        print(jira.get_current_user_as_assignee())
    elif jira_options.action == 'fetch-issuetypes':
        jira.update_issuetypes_cache()
        print('Updated local cache for issuetypes:')
        pprint(jira.get_issuetypes_names_from_cache())
    elif jira_options.action == 'get-issue':
        for issue_key in jira_options.issues:
            issue = jira.issues.get(key=issue_key)
            key = issue.get('key', 'N/A')
            title = issue.get('fields', {}).get('summary')
            print(f'[{key}] {title}')
    elif jira_options.action == 'get-project-keys':
        print('Dumped field values for:')
        pprint(jira.get_project_keys())
