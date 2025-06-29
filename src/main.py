#!/usr/bin/env python

import json
from pprint import pprint

from assistant import TextFormat
from mantis.jira.issue_field import IssueField
from mantis.mantis_client import MantisClient
from mantis.options_loader import OptionsLoader, parse_args

def main() -> None:
    options = OptionsLoader(parse_args())
    mantis = MantisClient(options)
    jira = mantis.jira

    if options.action == 'test-auth':
        jira.test_auth()
    elif options.action == 'me-as-assignee':
        print(jira.get_current_user_as_assignee())
    elif options.action == 'fetch-issuetypes':
        jira.system_config_loader.get_issuetypes()
        print('Updated local cache for issuetypes:')
        pprint(mantis.cache.get_issuetypes_from_system_cache())
    elif options.action == 'fetch-types':
        x = jira.system_config_loader.get_issuetypes()
        pprint (x)
    elif options.action == 'get-issue':
        for issue_key in options.args:
            issue = jira.issues.get(key=issue_key)
            key = issue.get('key', 'N/A')
            title = issue.get_field('summary')
            print(f'[{key}] {title}')
        mantis._no_read_cache = False
    elif options.action == 'validate-values':
        search_name = 'Casper'
        search_field = 'reporter'

        search_name = 'Commerce'
        search_field = 'cf[10001]' # 'team'

        validated_input = jira.validate_input(search_field, search_name)
    elif options.action == 'update-issue':
        for issue_key in options.args:
            issue = jira.issues.get(key=issue_key)
            data = {
                "fields": {
                    # "assignee": jira.get_current_user(),
                    "assignee": None,
                }
            }
            issue.update_field(data)
            mantis._no_read_cache = True
            issue = jira.issues.get(key=issue_key, force_skip_cache=True)
            key = issue.get('key', 'N/A')
            title = issue.get_field('summary')
            print(f'[{key}] {title}')
            mantis._no_read_cache = False
    elif options.action == 'compare':
        for issue_key in options.args:
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

    elif options.action == 'view-key':
        for issue_key in options.args:
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

    elif options.action == 'auto-complete':
        auto_complete_suggestions = jira.auto_complete.get_suggestions("reporter", 'Casper')
        print(auto_complete_suggestions)
    elif options.action == 'check-field':
        for issue_key in options.args:
            issue = jira.issues.get(key=issue_key)
            field = IssueField(issue, 'assignee')
            field.check_field()
    elif options.action == 'update-issue-from-draft':
        for issue_key in options.args:
            issue = jira.issues.get(key=issue_key)
            issue.update_from_draft()
    elif options.action == 'diff-issue-from-draft':
        for issue_key in options.args:
            issue = jira.issues.get(key=issue_key)
            issue.diff_issue_from_draft()
    elif options.action == 'get-project-keys':
        print ('Fetching from Jira...')
        resp = jira.system_config_loader.fetch_and_update_all_createmeta()
        print('Dumped field values for:')
        pprint(resp)
    elif options.action == 'inspect':
        jira.system_config_loader.inspect()
    elif options.action == 'compile-plugins':
        jira.system_config_loader.compile_plugins()
    elif options.action == 'load-plugins':
        from plugins import Plugins
        print(Plugins.all_plugins['plugins_test'].Schema(type='a', system='b'))  # type: ignore
        print(Plugins.plugins_test.Schema(type='a', system='b')) # type: ignore

        import plugins
        print(plugins.plugins_test.Schema(type='a', system='b')) # type: ignore

        from plugins.plugins_test import Schema
        print(Schema(type='a', system='b'))
        from plugins.new_epic import IssueModel  # type: ignore
        with open('tests/data/jira_cache/issues/ECS-1.json') as f:
            ecs_1 = json.load(f)
        print(IssueModel(**ecs_1))
        print(IssueModel.model_validate(ecs_1))
    elif options.action == 'invalidate-cache':
        mantis.cache.invalidate()
    elif options.action == 'reset':
        jira.warmup(delete_drafts=False)
    elif options.action == 'warmup-issues':
        issue_names = [f'{jira.project_name}-{i}' for i in range(1, 6)]
        jira.warmup_issues(*issue_names)
    elif options.action == 'attempt':
        jira.system_config_loader.attempt(issue_id = "ECS-1", issuetype_name = "epic")
    elif options.action == 'convert-markdown-to-jira':
        converted = mantis.assistant.convert_text_format("# This is a header\n\nThis is a paragraph with **bold** text and *italic* text.", TextFormat.JIRA)
        print(converted)
    elif options.action == 'validate-draft':
        data_ = jira.issues.get("ECS-1")
        data_.draft._validate_draft()
    elif options.action == 'update-draft':
        data_ = jira.issues.get("ECS-1")
        data_.draft.content = 'Trolololo'
    elif options.action == 'make-verbose':
        data_ = jira.issues.get("ECS-1")
        changes = data_.draft.make_verbose()
        pprint(changes)
    elif options.action == 'new':
        issue_type = options.args.pop(0).title() if options.args else 'Task'
        issue_title = ' '.join(options.args) or f'New {issue_type}'
        if issue_type not in jira.issues.allowed_types:
            raise ValueError(f'Issue type {issue_type} is not allowed. Allowed types: {jira.issues.allowed_types}')
        data = jira.issues.create(issuetype=issue_type, title=issue_title, data={})
    elif options.action == 'open-jira':
        jira.web()
    elif options.action == 'get-field-names':
        for issue_key in options.args:
            names = jira.get_field_names(issue_key)
            pprint(names['names'])
    else:
        print(f'Action {options.action} not recognized')

if __name__ == '__main__':
    main()
