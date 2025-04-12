#!/usr/bin/env python

import requests
import json
import requests

from typing import TYPE_CHECKING

from jira import JiraClient, JiraOptions, JiraAuth, parse_args

def log(*args):
    print(*args, file=sys.stderr)

if __name__ == '__main__':
    jira_option = JiraOptions(parse_args(), 'options.toml')
    auth = JiraAuth(jira_option)
    jira = JiraClient(jira_option, auth, requests)
    jira.test_auth()
