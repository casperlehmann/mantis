#!/usr/bin/env python

from pprint import pprint

from mantis.jira import JiraAuth, JiraClient, JiraOptions, parse_args

if __name__ == '__main__':
    jira_options = JiraOptions(parse_args(), 'options.toml')
    auth = JiraAuth(jira_options)
    jira = JiraClient(jira_options, auth)

    if jira_options.action == 'test-auth':
        jira.test_auth()
    elif jira_options.action == 'me-as-assignee':
        print(jira.get_current_user_as_assignee())
    elif jira_options.action == 'fetch-issuetypes':
        jira.system_config_loader.get_issuetypes()
        print('Updated local cache for issuetypes:')
        pprint(jira.cache.get_issuetypes_from_system_cache())
    elif jira_options.action == 'fetch-types':
        x = jira.system_config_loader.get_issuetypes()
        pprint (x)
    elif jira_options.action == 'get-issue':
        for issue_key in jira_options.issues:
            issue = jira.issues.get(key=issue_key)
            key = issue.get('key', 'N/A')
            title = issue.get_field('summary')
            print(f'[{key}] {title}')
        jira._no_read_cache = False
    elif jira_options.action == 'update-issue':
        for issue_key in jira_options.issues:
            issue = jira.issues.get(key=issue_key)
            data = {
                "fields": {
                    # "assignee": jira.get_current_user(),
                    "assignee": None,
                }
            }
            resp = issue.update_field(data)
            jira._no_read_cache = True
            issue = jira.issues.get(key=issue_key)
            key = issue.get('key', 'N/A')
            title = issue.get_field('summary')
            print(f'[{key}] {title}')
            jira._no_read_cache = False
    elif jira_options.action == 'update-issue-from-draft':
        for issue_key in jira_options.issues:
            issue = jira.issues.get(key=issue_key)
            draft_data = issue.draft.read_draft()
            print (f'draft_data: {draft_data}')

            local_vars = ('ignore', 'header')
            for field in draft_data.keys():
                value = draft_data.get(field)
                if field in local_vars:  # E.g. Local custom fields
                    continue
                if not value:  # E.g. parent not set
                    continue
                from_cache = issue.get_field(field, None)
                if not from_cache:
                    print (f'Field "{field}" not found in cache')
                print([value, from_cache])
                # assert value == from_cache
            assert draft_data.content == f'{draft_data.to_dict().get('content', '')}'
            assert not draft_data.content.startswith(f'# {draft_data.get('summary', '')}\n\n')
    elif jira_options.action == 'get-project-keys':
        print ('Fetching from Jira...')
        resp = jira.system_config_loader.fetch_and_update_all_createmeta()
        print('Dumped field values for:')
        pprint(resp)
    elif jira_options.action == 'inspect':
        jira.system_config_loader.inspect()
    elif jira_options.action == 'compile-plugins':
        jira.system_config_loader.compile_plugins()
    elif jira_options.action == 'load-plugins':
        from plugins import Plugins
        print(Plugins.all_plugins['plugins_test'].Schema(type='a', system='b'))
        print(Plugins.plugins_test.Schema(type='a', system='b')) # type: ignore

        import plugins
        print(plugins.plugins_test.Schema(type='a', system='b')) # type: ignore

        from plugins.plugins_test import Schema
        print(Schema(type='a', system='b'))
    elif jira_options.action == 'invalidate-cache':
        jira.cache.invalidate()
    elif jira_options.action == 'reset':
        jira.warmup()
    elif jira_options.action == 'attempt':
        jira.system_config_loader.attempt(issue_id = "ECS-1", issue_type = "epic")
    else:
        print(f'Action {jira_options.action} not recognized')

