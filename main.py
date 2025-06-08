#!/usr/bin/env python

from pprint import pprint

from mantis.jira import JiraAuth, JiraClient, JiraOptions, parse_args
from mantis.jira.issue_field import IssueField

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
    elif jira_options.action == 'validate-values':
        search_name = 'Casper'
        search_field = 'reporter'

        search_name = 'Commerce'
        search_field = 'cf[10001]' # 'team'

        validated_input = jira.validate_input(search_field, search_name)
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
            issue = jira.issues.get(key=issue_key, force_skip_cache=True)
            key = issue.get('key', 'N/A')
            title = issue.get_field('summary')
            print(f'[{key}] {title}')
            jira._no_read_cache = False
    elif jira_options.action == 'compare':
        for issue_key in jira_options.issues:
            issue = jira.issues.get(key=issue_key)
            print(f'Type: {issue.issuetype}')
            draft_data = issue.draft.read_draft()

            create_keys = issue.createmeta.fields.model_fields_set  # type: ignore
            edit_keys = issue.editmeta.fields.model_fields_set  # type: ignore
            editmeta_factory = issue._editmeta_factory.out_fields  # type: ignore
            createmeta_factory = issue._createmeta_factory.out_fields  # type: ignore
            issue_keys = set(issue.fields.keys())
            draft_keys = draft_data.keys()
            set_of_all_field_names = set(draft_keys).union(edit_keys).union(create_keys).union(issue_keys)
            line = '----------'
            print(20*' ', end=' ')
            print(f'{'create':^10} {'edit':^10} {'issue':^10} {'draft':^10} {'creat_fact':^10} {'edit_fact':^10}')
            for key in sorted(set_of_all_field_names):
                try:
                    from_create = '1' if issue.createmeta.fields.__getattribute__(key) else '0'  # type: ignore
                except AttributeError:
                    from_create = line
                try:
                    from_edit = '1' if issue.editmeta.fields.__getattribute__(key) else '0'  # type: ignore
                except AttributeError:
                    from_edit = line
                try:
                    from_issue = '1' if issue.fields[key] else '0'
                except KeyError:
                    from_issue = line
                try:
                    from_draft = '1' if draft_data[key] else '0'
                except KeyError:
                    from_draft = line
                try:
                    from_edit_fact = '1' if editmeta_factory[key] else '0'  # type: ignore
                except KeyError:
                    from_edit_fact = line
                try:
                    from_create_fact = '1' if createmeta_factory[key] else '0'  # type: ignore
                except KeyError:
                    from_create_fact = line
                if from_edit == from_create == line: continue
                print(f'{key[:20]:<20} {from_create:^10} {from_edit:^10} {from_issue:^10} {from_draft:^10} {from_create_fact:^10} {from_edit_fact:^10}')
            print(20*' ', end=' ')
            print(f'{'create':^10} {'edit':^10} {'issue':^10} {'draft':^10} {'creat_fact':^10} {'edit_fact':^10}')

    elif jira_options.action == 'view-key':
        for issue_key in jira_options.issues:
            issue = jira.issues.get(key=issue_key)
            draft_data = issue.draft.read_draft()

            create_keys = issue.createmeta.fields.model_fields_set  # type: ignore
            edit_keys = issue.editmeta.fields.model_fields_set  # type: ignore
            editmeta_factory = issue._editmeta_factory.out_fields  # type: ignore
            createmeta_factory = issue._createmeta_factory.out_fields  # type: ignore

            print(f'Type: {issue.issuetype}')

            key = 'reporter'
            print(f'Field: {key}')
            try:
                print(f'{'create':<10}', end=' ')
                print(issue.createmeta.fields.__getattribute__(key))  # type: ignore
            except AttributeError:
                print()
            try:
                print(f'{'edit':<10}', end=' ')
                print(issue.editmeta.fields.__getattribute__(key))  # type: ignore
            except AttributeError:
                print()
            try:
                print(f'{'issue':<10}', end=' ')
                print(issue.fields[key])
            except KeyError:
                print()
            try:
                print(f'{'draft':<10}', end=' ')
                print(draft_data[key])
            except KeyError:
                print()
            try:
                print(f'{'edit_fact':<10}', end=' ')
                print(editmeta_factory[key])
            except KeyError:
                print()
            try:
                print(f'{'creat_fact':<10}', end=' ')
                print(createmeta_factory[key])
            except KeyError:
                print()

    elif jira_options.action == 'auto-complete':
        auto_complete_suggestions = jira.auto_complete.get_suggestions("reporter", 'Casper')
        print(auto_complete_suggestions)
    elif jira_options.action == 'check-field':
        for issue_key in jira_options.issues:
            issue = jira.issues.get(key=issue_key)
            field = IssueField(issue, 'assignee')
            field.check_field()
    elif jira_options.action == 'update-issue-from-draft':
        for issue_key in jira_options.issues:
            issue = jira.issues.get(key=issue_key)
            issue.update_from_draft()
    elif jira_options.action == 'diff-issue-from-draft':
        for issue_key in jira_options.issues:
            issue = jira.issues.get(key=issue_key)
            issue.diff_issue_from_draft()
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
        jira.system_config_loader.attempt(issue_id = "ECS-1", issuetype_name = "epic")
    else:
        print(f'Action {jira_options.action} not recognized')

