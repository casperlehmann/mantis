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
            # print (f'draft_data: {draft_data}'.strip())
            # print()

            print('# issue.issuetype:')
            # pprint(issue.issuetype)
            print('# issue.editmeta:')
            # pprint(issue.editmeta)
            print('# issue.createmeta:')
            # pprint(issue.createmeta.createmeta_fields)
            made_create = issue.createmeta
            # print()
            # print("# made_create")
            # pprint(made_create)

            print()
            made_edit = issue.editmeta
            print("# made_edit")
            pprint(made_edit)
            print()

            print('dump editmeta')
            pprint(made_edit.model_dump())
            print()

            local_vars = ('ignore', 'header')
            for draft_field_key in draft_data.keys():
                if draft_field_key in local_vars:  # E.g. Local custom fields
                    continue
                value_from_draft = draft_data.get(draft_field_key)
                value_from_cache = issue.get_field(draft_field_key, 'N/A')
                
                if value_from_cache == 'N/A':
                    # https://caspertestaccount.atlassian.net/rest/api/latest/issue/ecs-1?expand=editmeta
                    # https://caspertestaccount.atlassian.net/rest/api/latest/issue/ecs-1/editmeta
                    # return default
                    # check editmeta
                    target_editmeta = issue.editmeta_data['fields'][draft_field_key]
                    target_editmeta = issue.editmeta.fields.model_fields_set  # type: ignore
                    # print('# target_editmeta')
                    # pprint(target_editmeta)
                    # {'hasDefaultValue': False,
                    #     'key': 'parent',
                    #     'name': 'Parent',
                    #     'operations': ['set'],
                    #     'required': False,
                    #     'schema': {'system': 'parent', 'type': 'issuelink'}}
                    print(f'draft_field_key {draft_field_key} in editmeta: {draft_field_key in issue.editmeta_data['fields']}')
                    print(f'draft_field_key {draft_field_key} in editmeta: {draft_field_key in issue.editmeta.fields.model_fields_set}')  # type: ignore


                print (f"# {issue_key} ", end="")
                # print ([field, type(value), value])
                extracted_from_cache = value_from_cache if isinstance(value_from_cache, str) else value_from_cache.get('displayName') or value_from_cache.get('name')
                if not value_from_draft:  # E.g. parent not set
                    print(f'# Not set   ({draft_field_key}) is None')
                elif not value_from_draft or value_from_draft == 'None' or value_from_draft == {draft_field_key: None}:
                    print(f'# None      ({draft_field_key}) is None')
                elif value_from_cache == 'N/A':
                    print(f'# Miss      ({draft_field_key}) not found in cache')
                elif not value_from_cache:
                    print(f'# Null      ({draft_field_key}) in cache but None')
                elif value_from_cache == 'None':
                    print(f'# Field     ({draft_field_key}) not found in cache')
                elif value_from_draft == value_from_cache:
                    print(f"# Same      ({draft_field_key}): {value_from_draft}")
                elif value_from_draft == extracted_from_cache:
                    print(f"# Extracted ({draft_field_key}): {value_from_draft}")
                else:
                    print(f"# Different: {draft_field_key}:")
                    print(f"{value_from_draft}")
                    pprint(value_from_cache)
                    # print ([field])
                    # print ([value])
                    # print ([from_cache])
                    input()
                # print([value, from_cache])
                # print()
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

