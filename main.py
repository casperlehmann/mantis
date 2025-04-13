#!/usr/bin/env python

from pprint import pprint

from mantis.jira import JiraClient, JiraOptions, JiraAuth, parse_args

from mantis.drafts import Draft

if __name__ == '__main__':
    jira_options = JiraOptions(parse_args(), 'options.toml')
    auth = JiraAuth(jira_options)
    jira = JiraClient(jira_options, auth)

    if jira_options.action == 'test-auth':
        jira.test_auth()
    elif jira_options.action == 'me-as-assignee':
        print(jira.get_current_user_as_assignee())
    elif jira_options.action == 'fetch-issuetypes':
        jira.system_config_loader.update_issuetypes_cache()
        print('Updated local cache for issuetypes:')
        pprint(jira.system_config_loader.get_issuetypes_names_from_cache())
    elif jira_options.action == 'get-issue':
        for issue_key in jira_options.issues:
            issue = jira.issues.get(key=issue_key)
            key = issue.get('key', 'N/A')
            title = issue.get('fields', {}).get('summary')
            print(f'[{key}] {title}')
            draft = Draft(issue)
    elif jira_options.action == 'get-project-keys':
        print ('Fetching from Jira...')
        resp = jira.system_config_loader.update_project_field_keys()
        print('Dumped field values for:')
        pprint(resp)
    elif jira_options.action == 'get-project-keys-from-cache':
        field_keys_collections = jira.system_config_loader.get_project_field_keys_from_cache()
        d = {}
        every = set()
        for issue_type, field_keys in field_keys_collections.items():
            print (f'# issue_type: {issue_type}')
            d[issue_type] = field_keys.show()
            every = every.union(set(d[issue_type]))

        print (f'{'':<20} - ', end='')
        for i in field_keys_collections.keys():
            print (f'{i:<10}', end = '')
        print()
        for each in every:
            print (f'{each:<20} - ', end='')
            for i in field_keys_collections.keys():
                print (f'{'1   ' if each in d[i] else '' :<10}', end = '')
            print()
        print (f'{'':<20} - ', end='')
        for i in field_keys_collections.keys():
            print (f'{i:<10}', end = '')
        print()

        '''
                     - Bug       Task      Story     Epic      Sub-Task
customfield_21729    - 1         1         1         1         1
assignee             - 1         1         1         1         1
customfield_10009    - 1         1         1         1         1
customfield_19300    - 1         1         1         1         1
attachment           - 1         1         1         1         1
customfield_10004    - 1         1         1         1         1
issuelinks           - 1         1         1         1         1
project              - 1         1         1         1         1
customfield_16500    - 1         1         1         1         1
customfield_21659    - 1         1         1         1         1
customfield_21107    -                               1
customfield_11400    - 1         1         1         1         1
customfield_21651    - 1         1         1         1         1
timetracking         - 1         1         1         1         1
summary              - 1         1         1         1         1
customfield_21108    -                               1
customfield_21051    - 1         1         1         1         1
customfield_24241    - 1         1         1         1         1
customfield_20866    - 1         1         1         1         1
customfield_24837    - 1         1         1                   1
customfield_21564    - 1         1         1                   1
components           - 1         1         1         1         1
customfield_11401    -                               1
customfield_16101    - 1         1         1         1         1
priority             - 1         1         1         1         1
customfield_20987    -                               1
customfield_24276    - 1         1         1                   1
customfield_24971    - 1         1         1         1         1
customfield_21848    -                               1
customfield_20524    - 1         1         1         1         1
customfield_19953    - 1         1         1         1         1
customfield_16000    - 1         1         1         1         1
customfield_24030    -                               1
customfield_21692    - 1         1         1         1         1
fixVersions          - 1         1         1         1         1
labels               - 1         1         1         1         1
customfield_20523    - 1         1         1         1         1
customfield_19880    - 1         1         1         1         1
customfield_19971    - 1         1         1         1         1
customfield_20016    - 1         1         1         1         1
description          - 1         1         1         1         1
parent               - 1         1         1         1         1
issuetype            - 1         1         1         1         1
customfield_20090    -                               1
                     - Bug       Task      Story     Epic      Sub-Task
'''

