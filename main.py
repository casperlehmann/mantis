#!/usr/bin/env python

import requests
import json
import requests

from pprint import pprint
from typing import TYPE_CHECKING

from jira import JiraClient, JiraOptions, JiraAuth, parse_args
from jira import fetch_enums

def log(*args):
    print(*args, file=sys.stderr)

if __name__ == '__main__':
    jira_option = JiraOptions(parse_args(), 'options.toml')
    auth = JiraAuth(jira_option)
    jira = JiraClient(jira_option, auth, requests)
    jira.test_auth()

    types_filter = lambda d: int(d['id']) < 100 and d['name'] in ('Bug', 'Task', 'Epic', 'Story', 'Incident', 'New Feature', 'Sub-Task')
    mapping = {'id': 'id', 'description': 'description', 'untranslatedName': 'name'}
    cast = {'id': int}
    issue_enums = fetch_enums(jira, endpoint = 'issuetype', filter = types_filter, mapping = mapping, cast = cast)
    pprint(issue_enums)
