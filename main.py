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
    else:
        print(f'Action {jira_options.action} not recognized')

